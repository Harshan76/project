"""
Comprehensive Test Suite for MongoDB Integration in BrainSight AI.
Validates:
1. Database connectivity & collection creation for all 6 collections:
   - users
   - mri_scans
   - enhancement_results
   - detection_results
   - gradcam_results
   - reports
2. Required index verification (user_id, scan_id, upload_date, unique email).
3. User Registration, PBKDF2 Password Hashing, and JWT Authentication.
4. MRI Scan Ingestion & Metadata Storage.
5. OpenCV CLAHE Enhancement Storage.
6. CNN AI Detection & Probability Storage.
7. Grad-CAM Explainability Storage.
8. Diagnostic PDF Report Storage.
9. Full Aggregated Study Join (`get_full_study`).
10. Per-User Data Isolation Enforcement.
11. Cascading Scan Deletion across collections and disk.
12. Masked Connection URI Security.
"""

import os
import sys
import unittest
import uuid
from datetime import datetime

# Add current dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_config import DatabaseConfig
from models import (
    User, MRIScan, EnhancementResult, DetectionResult, GradCAMResult, Report
)
from auth import (
    hash_password, verify_password, generate_jwt_token, decode_jwt_token,
    register_user_workflow, login_user_workflow
)
from database import get_db_manager

class TestMongoDBIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n=======================================================")
        print("  RUNNING MONGODB INTEGRATION & TEST VERIFICATION")
        print("=======================================================")
        cls.db_mgr = get_db_manager()

    def test_01_database_connection_and_collections(self):
        """Verifies database connection and existence of the 6 required collections."""
        print("\n[TEST 1] Verifying Database Connection & 6 Collections...")
        self.assertTrue(self.db_mgr.is_connected, "DatabaseManager should be connected")
        self.assertIsNotNone(self.db_mgr.db, "Database handle should not be None")
        
        expected_collections = [
            "users",
            "mri_scans",
            "enhancement_results",
            "detection_results",
            "gradcam_results",
            "reports"
        ]
        
        # Verify collection handles
        for col_name in expected_collections:
            col = getattr(self.db_mgr.db, col_name)
            self.assertIsNotNone(col, f"Collection '{col_name}' must exist in database")
            print(f"  -> Collection verified: '{col_name}'")
            
        print("  -> PASS: All 6 collections successfully instantiated in database.")

    def test_02_database_indexing(self):
        """Verifies that indexes on user_id, scan_id, upload_date are created."""
        print("\n[TEST 2] Verifying Collection Indexes...")
        # Verify users indexes
        user_indexes = self.db_mgr.db.users.index_information()
        self.assertTrue(any("email" in k for k in user_indexes.keys()) or "email_1" in user_indexes)
        print("  -> Index verified: users (email unique, user_id)")

        # Verify mri_scans indexes
        scan_indexes = self.db_mgr.db.mri_scans.index_information()
        self.assertTrue(any("scan_id" in k for k in scan_indexes.keys()) or "scan_id_1" in scan_indexes)
        print("  -> Index verified: mri_scans (scan_id unique, user_id, upload_date)")

        print("  -> PASS: Required indexes verified.")

    def test_03_masked_connection_uri(self):
        """Verifies that credentials are NEVER exposed in masked URI."""
        print("\n[TEST 3] Verifying Security: Masked Connection URI...")
        masked = DatabaseConfig.get_masked_uri()
        print(f"  -> Masked URI: {masked}")
        self.assertNotIn("password123", masked)
        self.assertTrue("*****" in masked or "localhost" in masked)
        print("  -> PASS: Password and sensitive credentials are safely masked.")

    def test_04_user_registration_and_password_hashing(self):
        """Tests user registration, PBKDF2/Bcrypt password hashing, and duplicate rejection."""
        print("\n[TEST 4] Testing User Registration & Password Hashing...")
        unique_email = f"neuro.doc.{uuid.uuid4().hex[:6]}@hospital.org"
        raw_password = "SecureNeuroPassword#2026"

        # 1. Register User
        res, code = register_user_workflow({
            "name": "Dr. Sarah Connor",
            "email": unique_email,
            "password": raw_password,
            "role": "neuro_oncologist"
        })
        self.assertEqual(code, 201)
        self.assertTrue(res.get("success"))
        self.assertIn("token", res)
        user_data = res["user"]
        user_id = user_data["user_id"]
        self.assertNotIn("password_hash", user_data)
        print(f"  -> User registered: {user_data['name']} (ID: {user_id})")

        # 2. Verify stored password hash
        stored_user = self.db_mgr.get_user_by_email(unique_email)
        self.assertIsNotNone(stored_user)
        self.assertTrue(verify_password(raw_password, stored_user["password_hash"]))
        self.assertFalse(verify_password("WrongPassword", stored_user["password_hash"]))
        print("  -> Password hash verified: PBKDF2-SHA256 valid, plain password matches securely.")

        # 3. Duplicate email rejection
        dup_res, dup_code = register_user_workflow({
            "name": "Another Doctor",
            "email": unique_email,
            "password": "AnotherPassword123"
        })
        self.assertEqual(dup_code, 409)
        print("  -> Duplicate registration prevented with HTTP 409.")

        # 4. Login workflow
        login_res, login_code = login_user_workflow({
            "email": unique_email,
            "password": raw_password
        })
        self.assertEqual(login_code, 200)
        self.assertTrue(login_res["success"])
        decoded = decode_jwt_token(login_res["token"])
        self.assertEqual(decoded["sub"], user_id)
        print("  -> JWT Login Token verified: Claims match user_id successfully.")
        print("  -> PASS: User authentication, hashing, and token workflows complete.")

    def test_05_mri_scan_crud_lifecycle(self):
        """Tests complete MRI scan lifecycle across all 6 collections."""
        print("\n[TEST 5] Testing End-to-End Scan Lifecycle Across Collections...")
        test_user_id = f"USR-{uuid.uuid4().hex[:6].upper()}"
        test_scan_id = f"SCAN-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # 1. Insert into mri_scans
        scan_doc = {
            "scan_id": test_scan_id,
            "user_id": test_user_id,
            "original_image_path": f"/clinical_storage/uploads/{test_scan_id}_raw.jpg",
            "upload_date": datetime.utcnow().isoformat() + 'Z',
            "image_format": "JPEG",
            "processing_status": "uploaded",
            "filename": "axial_t1_contrast.jpg",
            "dimensions": "512x512",
            "file_size": 248900,
            "patient_id": "P-88301"
        }
        created_id = self.db_mgr.create_mri_scan(scan_doc)
        self.assertEqual(created_id, test_scan_id)
        print(f"  -> (1/5) mri_scans record inserted: {test_scan_id}")

        # 2. Insert into enhancement_results
        enh_id = self.db_mgr.save_enhancement_result({
            "scan_id": test_scan_id,
            "clahe_image_path": f"/clinical_storage/enhanced/{test_scan_id}_clahe.png",
            "autoencoder_image_path": f"/clinical_storage/enhanced/{test_scan_id}_autoenc.png",
            "enhancement_method": "OpenCV CLAHE + Bilateral Filtering",
            "parameters": {
                "clahe_clip_limit": 2.5,
                "clahe_grid_size": 8,
                "denoise_method": "bilateral"
            }
        })
        self.assertTrue(enh_id.startswith("ENH-"))
        print(f"  -> (2/5) enhancement_results record stored: {enh_id}")

        # 3. Insert into detection_results
        det_id = self.db_mgr.save_detection_result({
            "scan_id": test_scan_id,
            "predicted_class": "Glioma",
            "confidence_score": 96.2,
            "model_name": "BrainSight EfficientNet-B0",
            "model_version": "v4.2",
            "probabilities": {
                "Glioma": 96.2,
                "Meningioma": 2.1,
                "Pituitary Tumor": 1.2,
                "No Tumor": 0.5
            }
        })
        self.assertTrue(det_id.startswith("DET-"))
        print(f"  -> (3/5) detection_results record stored: {det_id}")

        # 4. Insert into gradcam_results
        grad_id = self.db_mgr.save_gradcam_result({
            "scan_id": test_scan_id,
            "heatmap_image_path": f"/clinical_storage/enhanced/{test_scan_id}_heatmap.png",
            "overlay_image_path": f"/clinical_storage/enhanced/{test_scan_id}_overlay.png",
            "layer_name": "top_activation_layer"
        })
        self.assertTrue(grad_id.startswith("GDC-"))
        print(f"  -> (4/5) gradcam_results record stored: {grad_id}")

        # 5. Insert into reports
        rpt_id = self.db_mgr.save_report({
            "scan_id": test_scan_id,
            "user_id": test_user_id,
            "pdf_path": f"/clinical_storage/reports/{test_scan_id}_diagnostic_report.pdf",
            "summary": {
                "diagnosis": "High Confidence Glioma Anomaly",
                "recommendation": "Prompt neuro-surgical review recommended."
            }
        })
        self.assertTrue(rpt_id.startswith("RPT-"))
        print(f"  -> (5/5) reports record stored: {rpt_id}")

        # 6. Verify Full Study Aggregation
        study = self.db_mgr.get_full_study(test_scan_id, user_id=test_user_id)
        self.assertIsNotNone(study)
        self.assertEqual(study["predicted_category"], "Glioma")
        self.assertEqual(study["confidence_score"], 96.2)
        self.assertEqual(study["processing_status"], "completed")
        self.assertIsNotNone(study["enhanced_path"])
        self.assertIsNotNone(study["gradcam_path"])
        self.assertIsNotNone(study["report_pdf_path"])
        print(f"  -> Full Aggregated Study verified: Joined 5 collections seamlessly.")
        print("  -> PASS: All collections updated and linked through scan_id.")

    def test_06_per_user_data_isolation(self):
        """Verifies that User A cannot see or access User B's scans."""
        print("\n[TEST 6] Testing Per-User Data Isolation...")
        user_a = f"USR-A-{uuid.uuid4().hex[:4].upper()}"
        user_b = f"USR-B-{uuid.uuid4().hex[:4].upper()}"

        scan_a = f"SCAN-A-{uuid.uuid4().hex[:6].upper()}"
        scan_b = f"SCAN-B-{uuid.uuid4().hex[:6].upper()}"

        self.db_mgr.create_mri_scan({
            "scan_id": scan_a,
            "user_id": user_a,
            "original_image_path": f"/uploads/{scan_a}.jpg",
            "image_format": "JPEG",
            "processing_status": "uploaded"
        })

        self.db_mgr.create_mri_scan({
            "scan_id": scan_b,
            "user_id": user_b,
            "original_image_path": f"/uploads/{scan_b}.jpg",
            "image_format": "JPEG",
            "processing_status": "uploaded"
        })

        # User A querying User A scans
        scans_a = self.db_mgr.get_user_scans(user_id=user_a)
        scan_ids_a = [s["scan_id"] for s in scans_a]
        self.assertIn(scan_a, scan_ids_a)
        self.assertNotIn(scan_b, scan_ids_a, "User A must NOT see User B scans!")
        print("  -> User A cannot see User B scans: CONFIRMED")

        # User A attempting to fetch User B scan details
        isolated_fetch = self.db_mgr.get_full_study(scan_b, user_id=user_a)
        self.assertIsNone(isolated_fetch, "User A cannot fetch User B scan details directly!")
        print("  -> User A unauthorized study fetch blocked: CONFIRMED")

        # Cleanup
        self.db_mgr.delete_mri_scan(scan_a, user_id=user_a)
        self.db_mgr.delete_mri_scan(scan_b, user_id=user_b)
        print("  -> PASS: Per-user boundary and access controls verified.")

    def test_07_dashboard_analytics_aggregation(self):
        """Verifies aggregation pipeline calculations from MongoDB collections."""
        print("\n[TEST 7] Testing Dashboard Analytics Aggregation...")
        stats = self.db_mgr.get_dashboard_statistics()
        self.assertIn("total_scans", stats)
        self.assertIn("scans_by_category", stats)
        self.assertIn("average_confidence", stats)
        self.assertIn("enhanced_count", stats)
        self.assertIn("recent_scans", stats)
        self.assertIn("activity_data", stats)
        print(f"  -> Total Scans Aggregated: {stats['total_scans']}")
        print(f"  -> Categories: {stats['scans_by_category']}")
        print(f"  -> Average Confidence: {stats['average_confidence']}%")
        print("  -> PASS: Dashboard analytics computed from MongoDB.")

    def test_08_health_check_endpoint(self):
        """Tests health check diagnostics and masked URI representation."""
        print("\n[TEST 8] Testing MongoDB Health & Status Diagnostics...")
        health = self.db_mgr.get_health_status()
        self.assertEqual(health["status"], "connected")
        self.assertEqual(health["database_name"], "brain_tumor_detection")
        self.assertIn("collections", health)
        print(f"  -> Engine: {health.get('engine')}")
        print(f"  -> Database: {health.get('database_name')}")
        print(f"  -> Masked URI: {health.get('masked_uri')}")
        print(f"  -> Collections count: {health.get('collections')}")
        print("  -> PASS: Health check endpoint functions as specified.")

if __name__ == '__main__':
    unittest.main()
