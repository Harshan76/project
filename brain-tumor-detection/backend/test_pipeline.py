import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db, create_scan, update_scan, get_scan, get_dashboard_stats, delete_scan
from services.image_enhancement import enhance_mri_image
from services.prediction import predict_tumor, is_model_available, load_tumor_model
from services.gradcam import create_gradcam_overlay
from services.report_generator import generate_pdf_report

def main():
    print("--- 1. Testing Model Availability ---")
    avail, path = is_model_available()
    print(f"Model available: {avail}, Path: {path}")
    assert avail, "Model weights should be available!"

    print("\n--- 2. Testing Database Init ---")
    init_db()
    print("SQLite schema initialized.")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    sample_img = os.path.join(base_dir, 'sample_mris', 'sample_glioma.jpg')
    out_enh_dir = os.path.join(base_dir, 'enhanced_images')
    out_rep_dir = os.path.join(base_dir, 'reports')

    print("\n--- 3. Testing OpenCV Image Enhancement ---")
    enh_res = enhance_mri_image(sample_img, out_enh_dir, 'TEST-001')
    print("Enhanced image created:", enh_res['enhanced_path'])
    print("Comparison image created:", enh_res['comparison_path'])
    assert os.path.exists(enh_res['enhanced_path'])
    assert os.path.exists(enh_res['comparison_path'])

    print("\n--- 4. Testing CNN Model Prediction ---")
    pred_res = predict_tumor(enh_res['enhanced_path'])
    print(f"Predicted Category: {pred_res['predicted_category']} (Confidence: {pred_res['confidence_score']}%)")
    print("Differential Probabilities:", pred_res['probabilities'])

    print("\n--- 5. Testing Grad-CAM Generation ---")
    model = load_tumor_model()
    grad_res = create_gradcam_overlay(enh_res['enhanced_path'], model, out_enh_dir, 'TEST-001', class_index=pred_res['class_index'])
    print("Grad-CAM overlay created:", grad_res['gradcam_path'])
    print("Grad-CAM panel created:", grad_res['panel_path'])
    assert os.path.exists(grad_res['gradcam_path'])
    assert os.path.exists(grad_res['panel_path'])

    print("\n--- 6. Testing Structured PDF Report Generation ---")
    scan_record = {
        'scan_id': 'TEST-001',
        'patient_id': 'PAT-TEST-99',
        'filename': 'sample_glioma.jpg',
        'original_path': sample_img,
        'enhanced_path': enh_res['enhanced_path'],
        'gradcam_path': grad_res['gradcam_path'],
        'predicted_category': pred_res['predicted_category'],
        'confidence_score': pred_res['confidence_score'],
        'probabilities': pred_res['probabilities'],
        'enhancement_params': enh_res['parameters'],
        'created_at': '2026-11-13T14:35:00'
    }
    rep_res = generate_pdf_report(scan_record, out_rep_dir)
    print("PDF Report successfully created:", rep_res['pdf_path'])
    assert os.path.exists(rep_res['pdf_path'])

    print("\n--- 7. Testing Database Persistence & Dashboard Stats ---")
    create_scan({
        'scan_id': 'TEST-001',
        'filename': 'sample_glioma.jpg',
        'original_path': sample_img,
        'created_at': '2026-11-13T14:35:00',
        'dimensions': '224x224',
        'file_size': 14032,
        'patient_id': 'PAT-TEST-99'
    })
    update_scan('TEST-001', {
        'enhanced_path': enh_res['enhanced_path'],
        'gradcam_path': grad_res['gradcam_path'],
        'predicted_category': pred_res['predicted_category'],
        'confidence_score': pred_res['confidence_score'],
        'probabilities': pred_res['probabilities'],
        'report_text': rep_res['report_text'],
        'report_pdf_path': rep_res['pdf_path']
    })
    
    saved_scan = get_scan('TEST-001')
    print("Saved Scan Record in SQLite:", saved_scan['scan_id'], saved_scan['predicted_category'])
    
    stats = get_dashboard_stats()
    print("Dashboard Stats:", stats)
    assert stats['total_scans'] >= 1
    
    print("\n=======================================================")
    print("SUCCESS: ALL PIPELINES, OPENCV, CNN, GRAD-CAM, PDF, AND DB VERIFIED!")
    print("=======================================================")

if __name__ == '__main__':
    main()
