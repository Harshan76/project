import os
import uuid
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app, g
from werkzeug.utils import secure_filename
from PIL import Image

from database.db import (
    create_scan, update_scan, get_scan, get_all_scans, delete_scan, get_dashboard_stats
)
from database import get_db_manager
from auth import (
    token_required, register_user_workflow, login_user_workflow
)
from services.image_enhancement import enhance_mri_image
from services.prediction import predict_tumor, is_model_available, CLASS_NAMES
from services.gradcam import create_gradcam_overlay
from services.report_generator import generate_report_content, generate_pdf_report

api_bp = Blueprint('api', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# =============================================================================
# AUTHENTICATION & USER MANAGEMENT ENDPOINTS
# =============================================================================

@api_bp.route('/auth/register', methods=['POST'])
def register():
    """Registers a new user into MongoDB users collection."""
    data = request.get_json() or {}
    resp, status_code = register_user_workflow(data)
    return jsonify(resp), status_code

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """Authenticates a user and returns a signed JWT token."""
    data = request.get_json() or {}
    resp, status_code = login_user_workflow(data)
    return jsonify(resp), status_code

@api_bp.route('/auth/me', methods=['GET'])
@token_required(strict=False)
def get_current_user_profile():
    """Returns the profile of the currently authenticated user."""
    user = getattr(request, 'current_user', None) or g.get('current_user')
    return jsonify({
        "success": True,
        "user": user
    }), 200

# =============================================================================
# DATABASE HEALTH & MONGODB DIAGNOSTICS
# =============================================================================

@api_bp.route('/database/status', methods=['GET'])
def database_status():
    """Returns MongoDB connection status, collections, and masked URI."""
    db_mgr = get_db_manager()
    status = db_mgr.get_health_status()
    return jsonify({
        "success": True,
        "database": status
    }), 200

# =============================================================================
# SYSTEM HEALTH & STATUS
# =============================================================================

@api_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint returning exact requirement."""
    return jsonify({
        "status": "success",
        "message": "Backend is running"
    }), 200

@api_bp.route('/model/status', methods=['GET'])
def model_status():
    available, path = is_model_available()
    file_size = os.path.getsize(path) if available else 0
    return jsonify({
        "model_available": available,
        "model_path": path,
        "file_size_bytes": file_size,
        "classes": CLASS_NAMES,
        "input_shape": [224, 224, 3],
        "setup_instruction": "Run 'python train_model.py' to train or calibrate the CNN model on the Brain Tumor MRI dataset." if not available else "Model is loaded and ready for inference."
    })

@api_bp.route('/upload', methods=['POST'])
@token_required(strict=False)
def upload_mri():
    user = getattr(request, 'current_user', None) or g.get('current_user') or {}
    user_id = user.get('user_id', 'USR-CLINICIAN-001')

    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if not allowed_file(file.filename):
        return jsonify({
            "error": "Invalid file format. Allowed formats: JPG, JPEG, PNG, BMP"
        }), 400

    filename = secure_filename(file.filename)
    scan_id = f"SCAN-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    patient_id = request.form.get('patient_id') or f"PAT-{datetime.now().strftime('%y%m%d%H%M')}"
    
    upload_dir = os.path.join(current_app.root_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    saved_filename = f"{scan_id}_{filename}"
    file_path = os.path.join(upload_dir, saved_filename)
    file.save(file_path)
    
    # Read dimensions and size
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            dimensions = f"{width}x{height}"
            fmt = img.format or 'JPEG'
    except Exception:
        dimensions = "Unknown"
        fmt = 'JPEG'
        
    file_size = os.path.getsize(file_path)
    
    # Persist in MongoDB mri_scans and SQLite
    create_scan({
        "scan_id": scan_id,
        "user_id": user_id,
        "filename": filename,
        "original_path": file_path,
        "created_at": datetime.utcnow().isoformat(),
        "dimensions": dimensions,
        "file_size": file_size,
        "patient_id": patient_id,
        "image_format": fmt
    })
    
    return jsonify({
        "success": True,
        "scan_id": scan_id,
        "user_id": user_id,
        "filename": filename,
        "file_url": f"/uploads/{saved_filename}",
        "original_url": f"/uploads/{saved_filename}",
        "dimensions": dimensions,
        "file_size": file_size,
        "patient_id": patient_id,
        "created_at": datetime.utcnow().isoformat()
    }), 201

@api_bp.route('/enhance', methods=['POST'])
def enhance():
    data = request.get_json() or {}
    scan_id = data.get('scan_id')
    if not scan_id:
        return jsonify({"error": "scan_id is required"}), 400
        
    scan = get_scan(scan_id)
    if not scan:
        return jsonify({"error": f"Scan with ID '{scan_id}' not found"}), 404
        
    input_path = scan.get('original_image_path') or scan.get('original_path')
    enhanced_dir = os.path.join(current_app.root_path, 'enhanced_images')
    
    # Extract params with defaults
    clahe_clip_limit = float(data.get('clahe_clip_limit', 2.5))
    clahe_grid_size = int(data.get('clahe_grid_size', 8))
    denoise_method = str(data.get('denoise_method', 'bilateral'))
    denoise_strength = int(data.get('denoise_strength', 7))
    sharpen_strength = float(data.get('sharpen_strength', 1.2))
    brightness = int(data.get('brightness', 5))
    apply_normalization = bool(data.get('apply_normalization', True))
    
    try:
        res = enhance_mri_image(
            input_path=input_path,
            output_dir=enhanced_dir,
            scan_id=scan_id,
            clahe_clip_limit=clahe_clip_limit,
            clahe_grid_size=clahe_grid_size,
            denoise_method=denoise_method,
            denoise_strength=denoise_strength,
            sharpen_strength=sharpen_strength,
            brightness=brightness,
            apply_normalization=apply_normalization
        )
        
        # Update record in DB
        update_scan(scan_id, {
            "enhanced_path": res['enhanced_path'],
            "enhancement_params": res['parameters']
        })
        
        return jsonify({
            "success": True,
            "scan_id": scan_id,
            "enhanced_url": f"/enhanced_images/{res['enhanced_filename']}",
            "comparison_url": f"/enhanced_images/{res['comparison_filename']}",
            "parameters": res['parameters']
        })
    except Exception as e:
        return jsonify({"error": f"Enhancement failed: {str(e)}"}), 500

@api_bp.route('/predict', methods=['POST'])
def predict():
    data = request.get_json() or {}
    scan_id = data.get('scan_id')
    use_enhanced = bool(data.get('use_enhanced', False))
    
    if not scan_id:
        return jsonify({"error": "scan_id is required"}), 400
        
    scan = get_scan(scan_id)
    if not scan:
        return jsonify({"error": f"Scan with ID '{scan_id}' not found"}), 404
        
    # Check model availability first
    available, model_path = is_model_available()
    if not available:
        return jsonify({
            "success": False,
            "error": "MODEL_NOT_TRAINED",
            "message": "Trained CNN weights not found in backend/models/brain_tumor_model.keras. Please run train_model.py to train or calibrate the model.",
            "setup_command": "python train_model.py"
        }), 503
        
    # Choose image target
    if use_enhanced and scan.get('enhanced_path') and os.path.exists(scan['enhanced_path']):
        target_path = scan['enhanced_path']
        used_image_type = "enhanced"
    else:
        target_path = scan.get('original_image_path') or scan.get('original_path')
        used_image_type = "original"
        
    try:
        from services.prediction import load_tumor_model
        model = load_tumor_model()
        
        # 1. Prediction
        pred_result = predict_tumor(target_path)
        
        # 2. Grad-CAM Generation
        gradcam_dir = os.path.join(current_app.root_path, 'enhanced_images')
        grad_res = create_gradcam_overlay(
            image_path=target_path,
            model=model,
            output_dir=gradcam_dir,
            scan_id=scan_id,
            class_index=pred_result['class_index']
        )
        
        # 3. Update DB
        update_scan(scan_id, {
            "predicted_category": pred_result['predicted_category'],
            "confidence_score": pred_result['confidence_score'],
            "probabilities": pred_result['probabilities'],
            "gradcam_path": grad_res['gradcam_path']
        })
        
        return jsonify({
            "success": True,
            "scan_id": scan_id,
            "used_image_type": used_image_type,
            "predicted_category": pred_result['predicted_category'],
            "confidence_score": pred_result['confidence_score'],
            "probabilities": pred_result['probabilities'],
            "gradcam_url": f"/enhanced_images/{grad_res['gradcam_filename']}",
            "panel_url": f"/enhanced_images/{grad_res['panel_filename']}",
            "model_architecture": pred_result['model_architecture']
        })
    except Exception as e:
        return jsonify({"error": f"Prediction or Grad-CAM failed: {str(e)}"}), 500

@api_bp.route('/generate-report', methods=['POST'])
def generate_report():
    data = request.get_json() or {}
    scan_id = data.get('scan_id')
    
    if not scan_id:
        return jsonify({"error": "scan_id is required"}), 400
        
    scan = get_scan(scan_id)
    if not scan:
        return jsonify({"error": f"Scan with ID '{scan_id}' not found"}), 404
        
    if not scan.get('predicted_category'):
        return jsonify({
            "error": "Scan has not been classified yet. Run /api/predict first."
        }), 400
        
    reports_dir = os.path.join(current_app.root_path, 'reports')
    
    try:
        report_res = generate_pdf_report(scan, reports_dir)
        
        # Save to DB
        update_scan(scan_id, {
            "report_text": report_res['report_text'],
            "report_pdf_path": report_res['pdf_path']
        })
        
        return jsonify({
            "success": True,
            "scan_id": scan_id,
            "report_text": report_res['report_text'],
            "pdf_url": f"/reports/{report_res['pdf_filename']}",
            "generative_mode": report_res['generative_mode']
        })
    except Exception as e:
        return jsonify({"error": f"Report generation failed: {str(e)}"}), 500

@api_bp.route('/history', methods=['GET'])
@token_required(strict=False)
def history():
    user = getattr(request, 'current_user', None) or g.get('current_user') or {}
    # If all_users=true is requested, show all; otherwise prioritize user's scans
    user_id = None if request.args.get('all_users') == 'true' else user.get('user_id')
    category = request.args.get('category')
    search = request.args.get('search')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    scans = get_all_scans(user_id=user_id, category=category, search=search, limit=limit, offset=offset)
    
    # Add URLs for frontend viewing
    formatted_scans = []
    for s in scans:
        orig_fn = os.path.basename(s['original_path']) if s.get('original_path') else None
        enh_fn = os.path.basename(s['enhanced_path']) if s.get('enhanced_path') else None
        grad_fn = os.path.basename(s['gradcam_path']) if s.get('gradcam_path') else None
        pdf_fn = os.path.basename(s['report_pdf_path']) if s.get('report_pdf_path') else None
        
        formatted_scans.append({
            **s,
            "original_url": f"/uploads/{orig_fn}" if orig_fn else None,
            "enhanced_url": f"/enhanced_images/{enh_fn}" if enh_fn else None,
            "gradcam_url": f"/enhanced_images/{grad_fn}" if grad_fn else None,
            "pdf_url": f"/reports/{pdf_fn}" if pdf_fn else None
        })
        
    return jsonify({
        "success": True,
        "count": len(formatted_scans),
        "scans": formatted_scans
    })

@api_bp.route('/history/<scan_id>', methods=['GET'])
@token_required(strict=False)
def get_history_item(scan_id):
    user = getattr(request, 'current_user', None) or g.get('current_user') or {}
    user_id = user.get('user_id')
    
    scan = get_scan(scan_id, user_id=user_id)
    if not scan:
        # Fallback without user_id filter in case it was created in demo session
        scan = get_scan(scan_id)
    if not scan:
        return jsonify({"error": f"Scan '{scan_id}' not found"}), 404
        
    orig_fn = os.path.basename(scan['original_path']) if scan.get('original_path') else None
    enh_fn = os.path.basename(scan['enhanced_path']) if scan.get('enhanced_path') else None
    grad_fn = os.path.basename(scan['gradcam_path']) if scan.get('gradcam_path') else None
    pdf_fn = os.path.basename(scan['report_pdf_path']) if scan.get('report_pdf_path') else None
    
    return jsonify({
        "success": True,
        "scan": {
            **scan,
            "original_url": f"/uploads/{orig_fn}" if orig_fn else None,
            "enhanced_url": f"/enhanced_images/{enh_fn}" if enh_fn else None,
            "gradcam_url": f"/enhanced_images/{grad_fn}" if grad_fn else None,
            "pdf_url": f"/reports/{pdf_fn}" if pdf_fn else None
        }
    })

@api_bp.route('/history/<scan_id>', methods=['DELETE'])
@token_required(strict=False)
def delete_history_item(scan_id):
    user = getattr(request, 'current_user', None) or g.get('current_user') or {}
    user_id = user.get('user_id')
    
    deleted = delete_scan(scan_id, user_id=user_id)
    if not deleted:
        return jsonify({"error": f"Scan '{scan_id}' not found or already deleted"}), 404
        
    return jsonify({
        "success": True,
        "message": f"Scan '{scan_id}' and all associated assets were permanently deleted.",
        "deleted_id": scan_id
    })

@api_bp.route('/dashboard/stats', methods=['GET'])
@token_required(strict=False)
def dashboard_stats():
    user = getattr(request, 'current_user', None) or g.get('current_user') or {}
    user_id = None if request.args.get('all_users') == 'true' else user.get('user_id')
    stats = get_dashboard_stats(user_id=user_id)
    return jsonify({
        "success": True,
        **stats
    })

@api_bp.route('/sample-images', methods=['GET'])
def sample_images():
    """Lists available sample MRI images to facilitate immediate evaluation and demo."""
    sample_dir = os.path.join(current_app.root_path, 'sample_mris')
    samples = []
    if os.path.exists(sample_dir):
        for fn in os.listdir(sample_dir):
            if allowed_file(fn):
                samples.append({
                    "filename": fn,
                    "url": f"/sample_mris/{fn}",
                    "label": fn.replace('sample_', '').replace('.jpg', '').replace('.png', '').replace('_', ' ').title()
                })
    return jsonify({
        "success": True,
        "samples": samples
    })
