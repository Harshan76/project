import os
import sys
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db, create_scan, update_scan
from services.image_enhancement import enhance_mri_image
from services.prediction import predict_tumor, load_tumor_model
from services.gradcam import create_gradcam_overlay
from services.report_generator import generate_pdf_report

def seed():
    init_db()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sample_dir = os.path.join(base_dir, 'sample_mris')
    uploads_dir = os.path.join(base_dir, 'uploads')
    enhanced_dir = os.path.join(base_dir, 'enhanced_images')
    reports_dir = os.path.join(base_dir, 'reports')
    
    samples = [
        ('sample_glioma.jpg', 'Glioma', 'PAT-202611-1042', 2),
        ('sample_meningioma.jpg', 'Meningioma', 'PAT-202611-2098', 4),
        ('sample_pituitary_tumor.jpg', 'Pituitary Tumor', 'PAT-202611-3811', 6),
        ('sample_no_tumor.jpg', 'No Tumor', 'PAT-202611-4402', 8)
    ]
    
    model = load_tumor_model()
    
    for filename, cat_label, pat_id, hours_ago in samples:
        src = os.path.join(sample_dir, filename)
        if not os.path.exists(src):
            continue
            
        scan_id = f"SCAN-20261113-{uuid.uuid4().hex[:6].upper()}"
        dest_filename = f"{scan_id}_{filename}"
        dest_path = os.path.join(uploads_dir, dest_filename)
        
        # Copy image to uploads
        with open(src, 'rb') as f_in, open(dest_path, 'wb') as f_out:
            f_out.write(f_in.read())
            
        created_time = (datetime.utcnow() - timedelta(hours=hours_ago)).isoformat()
        
        create_scan({
            'scan_id': scan_id,
            'filename': filename,
            'original_path': dest_path,
            'created_at': created_time,
            'dimensions': '224x224',
            'file_size': os.path.getsize(dest_path),
            'patient_id': pat_id
        })
        
        # Run enhancement
        enh_res = enhance_mri_image(dest_path, enhanced_dir, scan_id)
        
        # Run prediction
        pred_res = predict_tumor(enh_res['enhanced_path'])
        
        # Run Grad-CAM
        grad_res = create_gradcam_overlay(
            enh_res['enhanced_path'],
            model,
            enhanced_dir,
            scan_id,
            class_index=pred_res['class_index']
        )
        
        # Build scan record for report
        scan_record = {
            'scan_id': scan_id,
            'patient_id': pat_id,
            'filename': filename,
            'original_path': dest_path,
            'enhanced_path': enh_res['enhanced_path'],
            'gradcam_path': grad_res['gradcam_path'],
            'predicted_category': pred_res['predicted_category'],
            'confidence_score': pred_res['confidence_score'],
            'probabilities': pred_res['probabilities'],
            'enhancement_params': enh_res['parameters'],
            'created_at': created_time
        }
        
        rep_res = generate_pdf_report(scan_record, reports_dir)
        
        update_scan(scan_id, {
            'enhanced_path': enh_res['enhanced_path'],
            'gradcam_path': grad_res['gradcam_path'],
            'predicted_category': pred_res['predicted_category'],
            'confidence_score': pred_res['confidence_score'],
            'probabilities': pred_res['probabilities'],
            'report_text': rep_res['report_text'],
            'report_pdf_path': rep_res['pdf_path']
        })
        print(f"Seeded scan {scan_id}: {filename} -> {pred_res['predicted_category']}")

if __name__ == '__main__':
    seed()
