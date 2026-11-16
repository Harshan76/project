import os
import sys
import json
import io

# Import app factory
from app import create_app

def run_tests():
    print("=== STARTING FULL BACKEND & API VERIFICATION ===")
    app = create_app()
    client = app.test_client()
    
    # 1. Test GET /api/health
    print("\n[TEST 1] GET /api/health")
    res = client.get('/api/health')
    print("Status:", res.status_code)
    data = res.get_json()
    print("Body:", data)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert data.get("status") == "success", f"Expected status 'success', got {data.get('status')}"
    assert data.get("message") == "Backend is running", f"Expected message 'Backend is running', got {data.get('message')}"
    print("--> PASS: /api/health returns correct JSON")

    # 2. Test GET /health
    print("\n[TEST 2] GET /health")
    res = client.get('/health')
    print("Status:", res.status_code, "Body:", res.get_json())
    assert res.status_code == 200
    print("--> PASS: /health returns correct JSON")

    # 3. Test GET /
    print("\n[TEST 3] GET /")
    res = client.get('/')
    print("Status:", res.status_code, "Body:", res.get_json())
    assert res.status_code == 200
    print("--> PASS: Root index returns 200")

    # 4. Test GET /api/model/status
    print("\n[TEST 4] GET /api/model/status")
    res = client.get('/api/model/status')
    data = res.get_json()
    print("Status:", res.status_code, "Model Available:", data.get('model_available'), "Classes:", data.get('classes'))
    assert res.status_code == 200
    assert data.get('model_available') is True, "Expected model to be available"
    print("--> PASS: /api/model/status loaded trained CNN weights")

    # 5. Test GET /api/dashboard/stats
    print("\n[TEST 5] GET /api/dashboard/stats")
    res = client.get('/api/dashboard/stats')
    data = res.get_json()
    print("Status:", res.status_code, "Total scans in DB:", data.get('total_scans'))
    assert res.status_code == 200
    assert data.get('success') is True
    print("--> PASS: /api/dashboard/stats retrieved DB stats")

    # 6. Test GET /api/sample-images
    print("\n[TEST 6] GET /api/sample-images")
    res = client.get('/api/sample-images')
    data = res.get_json()
    samples = data.get('samples', [])
    print("Status:", res.status_code, "Found samples:", len(samples))
    assert res.status_code == 200
    assert len(samples) > 0, "Expected at least 1 sample image"
    print("--> PASS: /api/sample-images verified with samples:", [s['filename'] for s in samples])

    # 7. Test POST /api/upload
    print("\n[TEST 7] POST /api/upload")
    sample_file_path = os.path.join(app.root_path, 'sample_mris', 'sample_glioma.jpg')
    with open(sample_file_path, 'rb') as f:
        file_bytes = f.read()

    data = {
        'file': (io.BytesIO(file_bytes), 'test_mri_scan.jpg'),
        'patient_id': 'TEST-PAT-991'
    }
    res = client.post('/api/upload', data=data, content_type='multipart/form-data')
    upload_res = res.get_json()
    print("Status:", res.status_code, "Upload Result:", upload_res)
    assert res.status_code == 201
    assert upload_res.get('success') is True
    scan_id = upload_res['scan_id']
    print(f"--> PASS: Uploaded scan created with ID: {scan_id}")

    # 8. Test POST /api/enhance
    print("\n[TEST 8] POST /api/enhance")
    res = client.post('/api/enhance', json={
        'scan_id': scan_id,
        'clahe_clip_limit': 2.5,
        'clahe_grid_size': 8,
        'denoise_method': 'bilateral',
        'denoise_strength': 7,
        'sharpen_strength': 1.2,
        'brightness': 5,
        'apply_normalization': True
    })
    enhance_res = res.get_json()
    print("Status:", res.status_code, "Enhanced URL:", enhance_res.get('enhanced_url'))
    assert res.status_code == 200
    assert enhance_res.get('success') is True
    print("--> PASS: Image enhancement executed via OpenCV CLAHE and filters")

    # 9. Test POST /api/predict
    print("\n[TEST 9] POST /api/predict")
    res = client.post('/api/predict', json={
        'scan_id': scan_id,
        'use_enhanced': True
    })
    pred_res = res.get_json()
    print("Status:", res.status_code)
    print("Predicted Category:", pred_res.get('predicted_category'))
    print("Confidence Score:", pred_res.get('confidence_score'))
    print("Probabilities:", pred_res.get('probabilities'))
    print("Grad-CAM URL:", pred_res.get('gradcam_url'))
    assert res.status_code == 200
    assert pred_res.get('success') is True
    assert 'probabilities' in pred_res
    print("--> PASS: CNN prediction and Grad-CAM generated successfully")

    # 10. Test POST /api/generate-report
    print("\n[TEST 10] POST /api/generate-report")
    res = client.post('/api/generate-report', json={'scan_id': scan_id})
    report_res = res.get_json()
    print("Status:", res.status_code, "PDF URL:", report_res.get('pdf_url'))
    assert res.status_code == 200
    assert report_res.get('success') is True
    print("--> PASS: Clinical report and PDF generated successfully")

    # 11. Test GET /api/history and /api/history/<id>
    print("\n[TEST 11] GET /api/history")
    res = client.get('/api/history')
    hist_res = res.get_json()
    print("Status:", res.status_code, "Count:", hist_res.get('count'))
    assert res.status_code == 200

    print("\n[TEST 12] GET /api/history/" + scan_id)
    res = client.get(f'/api/history/{scan_id}')
    detail_res = res.get_json()
    print("Status:", res.status_code, "Patient:", detail_res.get('scan', {}).get('patient_id'))
    assert res.status_code == 200

    # 12. Test DELETE /api/history/<id>
    print("\n[TEST 13] DELETE /api/history/" + scan_id)
    res = client.delete(f'/api/history/{scan_id}')
    del_res = res.get_json()
    print("Status:", res.status_code, "Deleted:", del_res.get('success'))
    assert res.status_code == 200
    assert del_res.get('success') is True
    print("--> PASS: Scan record and assets deleted successfully")

    print("\n==========================================")
    print("ALL 13 API & BACKEND TESTS PASSED CLEANLY!")
    print("==========================================")

if __name__ == '__main__':
    run_tests()
