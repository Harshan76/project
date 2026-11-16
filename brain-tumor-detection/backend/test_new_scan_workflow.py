import os
import sys
import io
import json

from app import create_app
from database.db import get_scan, get_all_scans

def run_workflow_tests():
    print("=======================================================")
    print("  RUNNING VERIFICATION FOR MRI SCAN UPLOAD & NEW SCAN  ")
    print("=======================================================")
    app = create_app()
    client = app.test_client()

    # Load real sample image bytes
    sample_path = os.path.join(app.root_path, 'sample_mris', 'sample_meningioma.jpg')
    assert os.path.exists(sample_path), f"Sample file not found at {sample_path}"
    with open(sample_path, 'rb') as f:
        img_bytes_1 = f.read()

    sample_path_2 = os.path.join(app.root_path, 'sample_mris', 'sample_glioma.jpg')
    with open(sample_path_2, 'rb') as f:
        img_bytes_2 = f.read()

    # ----------------------------------------------------
    # TEST 1 & 2 & 3: File validation & Upload Scan 1
    # ----------------------------------------------------
    print("\n[TEST 1, 2, 3] Testing File Upload for Study #1...")
    data_1 = {
        'file': (io.BytesIO(img_bytes_1), 'patient_01_meningioma.jpg'),
        'patient_id': 'P-10101'
    }
    res_1 = client.post('/api/upload', data=data_1, content_type='multipart/form-data')
    assert res_1.status_code == 201, f"Expected 201, got {res_1.status_code}: {res_1.data}"
    body_1 = res_1.get_json()
    assert body_1.get('success') is True
    scan_id_1 = body_1['scan_id']
    file_url_1 = body_1['file_url']
    print(f"  -> Generated Scan ID: {scan_id_1}")
    print(f"  -> Saved file URL: {file_url_1}")
    print(f"  -> Image dimensions: {body_1.get('dimensions')}")
    assert scan_id_1.startswith("SCAN-")

    # Verify scan 1 is in SQLite
    db_scan_1 = get_scan(scan_id_1)
    assert db_scan_1 is not None, "Scan 1 was not persisted in SQLite"
    assert db_scan_1['filename'] == 'patient_01_meningioma.jpg'
    assert db_scan_1['patient_id'] == 'P-10101'
    print("  -> PASS: Scan #1 persisted in SQLite successfully")

    # ----------------------------------------------------
    # TEST 4: Enhance Scan 1
    # ----------------------------------------------------
    print(f"\n[TEST 4] Applying OpenCV CLAHE Enhancement to {scan_id_1}...")
    res_enh_1 = client.post('/api/enhance', json={
        'scan_id': scan_id_1,
        'clahe_clip_limit': 3.0,
        'clahe_grid_size': 8
    })
    assert res_enh_1.status_code == 200
    enh_body_1 = res_enh_1.get_json()
    assert enh_body_1.get('success') is True
    assert 'enhanced_url' in enh_body_1
    print(f"  -> Enhanced URL: {enh_body_1['enhanced_url']}")
    print("  -> PASS: Enhancement generated")

    # ----------------------------------------------------
    # TEST 5: Predict & Grad-CAM on Scan 1
    # ----------------------------------------------------
    print(f"\n[TEST 5] Running CNN Inference & Grad-CAM for {scan_id_1}...")
    res_pred_1 = client.post('/api/predict', json={
        'scan_id': scan_id_1,
        'use_enhanced': True
    })
    assert res_pred_1.status_code == 200
    pred_body_1 = res_pred_1.get_json()
    assert pred_body_1.get('success') is True
    cat_1 = pred_body_1['predicted_category']
    conf_1 = pred_body_1['confidence_score']
    print(f"  -> Prediction: {cat_1} ({conf_1}%)")
    print(f"  -> Grad-CAM URL: {pred_body_1['gradcam_url']}")
    print("  -> PASS: Prediction & Grad-CAM generated")

    # ----------------------------------------------------
    # TEST 6 & 7: "New Scan" workflow - Upload fresh Scan 2
    # ----------------------------------------------------
    print("\n[TEST 6, 7] Starting NEW SCAN workflow for Study #2...")
    data_2 = {
        'file': (io.BytesIO(img_bytes_2), 'patient_02_glioma.png'),
        'patient_id': 'P-20202'
    }
    res_2 = client.post('/api/upload', data=data_2, content_type='multipart/form-data')
    assert res_2.status_code == 201
    body_2 = res_2.get_json()
    assert body_2.get('success') is True
    scan_id_2 = body_2['scan_id']
    file_url_2 = body_2['file_url']

    print(f"  -> Generated New Scan ID: {scan_id_2}")
    print(f"  -> New file URL: {file_url_2}")
    assert scan_id_2 != scan_id_1, "New scan ID must be unique from previous scan!"
    assert file_url_2 != file_url_1, "New scan must have its own separate file asset!"

    # Verify Scan 2 in DB starts with clean state (no enhancement or prediction yet)
    db_scan_2 = get_scan(scan_id_2)
    assert db_scan_2 is not None
    assert db_scan_2['predicted_category'] is None, "New scan must NOT retain previous prediction!"
    assert db_scan_2['enhanced_path'] is None, "New scan must NOT retain previous enhancement!"
    print("  -> PASS: New scan state is cleanly separated and has no prior predictions or enhancements")

    # ----------------------------------------------------
    # TEST 8: Verify Scan 1 still exists in SQLite History
    # ----------------------------------------------------
    print("\n[TEST 8] Verifying Scan History retention...")
    res_hist = client.get('/api/history')
    assert res_hist.status_code == 200
    hist_body = res_hist.get_json()
    scans_in_db = [s['scan_id'] for s in hist_body.get('scans', [])]

    assert scan_id_1 in scans_in_db, f"Previous scan {scan_id_1} must still exist in history!"
    assert scan_id_2 in scans_in_db, f"New scan {scan_id_2} must also exist in history!"
    print(f"  -> Total scans in history registry: {hist_body['count']}")
    print(f"  -> Both {scan_id_1} and {scan_id_2} verified in SQLite database!")
    print("  -> PASS: Previous scan records are safely preserved without deletion")

    # ----------------------------------------------------
    # Clean up test scans
    # ----------------------------------------------------
    client.delete(f'/api/history/{scan_id_1}')
    client.delete(f'/api/history/{scan_id_2}')
    print("\n[CLEANUP] Deleted temporary test records cleanly.")

    print("\n=======================================================")
    print("  ALL 8 WORKFLOW & NEW SCAN TESTS PASSED SUCCESSFULLY!  ")
    print("=======================================================")

if __name__ == '__main__':
    run_workflow_tests()
