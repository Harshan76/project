"""
MongoDB Database Manager for BrainSight AI.
Connects Flask to MongoDB using PyMongo.
Manages the 6 core collections:
- users
- mri_scans
- enhancement_results
- detection_results
- gradcam_results
- reports
Provides schema initialization, indexing, validation, and CRUD operations with per-user data isolation.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from pymongo import MongoClient, ASCENDING, DESCENDING, errors
from database_config import DatabaseConfig
from models import (
    User, MRIScan, EnhancementResult, DetectionResult, GradCAMResult, Report
)

logger = logging.getLogger("brainsight.database")

class DatabaseManager:
    """
    Singleton Manager for PyMongo database operations.
    Supports MongoDB Atlas, Local MongoDB server, and in-memory mock fallback.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        if self._initialized:
            return

        self.uri = uri or DatabaseConfig.MONGODB_URI
        self.db_name = db_name or DatabaseConfig.MONGODB_DB_NAME
        self.client: Optional[MongoClient] = None
        self.db = None
        self.is_connected = False
        self.is_mock = False
        self.error_message: Optional[str] = None

        self._connect()
        self._ensure_indexes()
        self._initialized = True

    def _connect(self):
        """Initializes connection to MongoDB Atlas or local MongoDB."""
        DatabaseConfig.ensure_storage_dirs()
        masked_uri = DatabaseConfig.get_masked_uri()

        try:
            # Attempt live connection to MongoDB Atlas or local server
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=DatabaseConfig.MONGODB_SERVER_SELECTION_TIMEOUT_MS,
                connectTimeoutMS=DatabaseConfig.MONGODB_CONNECT_TIMEOUT_MS,
                socketTimeoutMS=DatabaseConfig.MONGODB_SOCKET_TIMEOUT_MS,
                maxPoolSize=DatabaseConfig.MONGODB_MAX_POOL_SIZE
            )
            # Verify server responsiveness with ping
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.is_connected = True
            self.is_mock = False
            self.error_message = None
            logger.info(f"Successfully connected to MongoDB ({masked_uri}) -> DB: {self.db_name}")
            print(f"[MongoDB] Connected successfully to '{self.db_name}' at {masked_uri}")

        except Exception as e:
            if self.client is not None:
                try:
                    self.client.close()
                except Exception:
                    pass
            self.error_message = str(e)
            logger.warning(f"Could not connect to live MongoDB at {masked_uri}: {e}")
            print(f"[MongoDB] Live server not available ({masked_uri}): {e}")

            if DatabaseConfig.ALLOW_MOCK_FALLBACK:
                try:
                    import mongomock
                    self.client = mongomock.MongoClient()
                    self.db = self.client[self.db_name]
                    self.is_connected = True
                    self.is_mock = True
                    print(f"[MongoDB] Activated resilient mock engine for '{self.db_name}' (Atlas URI ready for production).")
                except Exception as mock_err:
                    self.is_connected = False
                    self.db = None
                    print(f"[MongoDB Error] Mock initialization failed: {mock_err}")
            else:
                self.is_connected = False
                self.db = None

    def _ensure_indexes(self):
        """Sets up required indexes for query performance, unique constraints, and user isolation."""
        if not self.is_connected or self.db is None:
            return

        try:
            # 1. users collection indexes
            self.db.users.create_index([("email", ASCENDING)], unique=True)
            self.db.users.create_index([("user_id", ASCENDING)], unique=True)

            # 2. mri_scans collection indexes
            self.db.mri_scans.create_index([("scan_id", ASCENDING)], unique=True)
            self.db.mri_scans.create_index([("user_id", ASCENDING)])
            self.db.mri_scans.create_index([("upload_date", DESCENDING)])
            self.db.mri_scans.create_index([("user_id", ASCENDING), ("upload_date", DESCENDING)])

            # 3. enhancement_results collection indexes
            self.db.enhancement_results.create_index([("enhancement_id", ASCENDING)], unique=True)
            self.db.enhancement_results.create_index([("scan_id", ASCENDING)])

            # 4. detection_results collection indexes
            self.db.detection_results.create_index([("detection_id", ASCENDING)], unique=True)
            self.db.detection_results.create_index([("scan_id", ASCENDING)])
            self.db.detection_results.create_index([("predicted_class", ASCENDING)])

            # 5. gradcam_results collection indexes
            self.db.gradcam_results.create_index([("gradcam_id", ASCENDING)], unique=True)
            self.db.gradcam_results.create_index([("scan_id", ASCENDING)])

            # 6. reports collection indexes
            self.db.reports.create_index([("report_id", ASCENDING)], unique=True)
            self.db.reports.create_index([("scan_id", ASCENDING)])
            self.db.reports.create_index([("user_id", ASCENDING)])

            print("[MongoDB] Verified 6 collection indexes (user_id, scan_id, upload_date, unique constraints).")
        except Exception as e:
            logger.warning(f"Index creation notice: {e}")

    # =========================================================================
    # 1. USERS COLLECTION CRUD
    # =========================================================================

    def create_user(self, user_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new user record in MongoDB."""
        if not self.is_connected:
            raise RuntimeError("Database is disconnected")
        
        # Validate through model
        user = User.from_dict(user_dict)
        user.validate()
        
        doc = user.to_dict(include_sensitive=True)
        try:
            self.db.users.insert_one(doc)
            return user.to_dict(include_sensitive=False)
        except errors.DuplicateKeyError:
            raise ValueError(f"User with email '{user.email}' or ID '{user.user_id}' already exists.")

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves user by user_id."""
        if not self.is_connected:
            return None
        doc = self.db.users.find_one({"user_id": user_id}, {"_id": 0})
        return doc

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieves user by email address (includes password_hash for auth)."""
        if not self.is_connected:
            return None
        doc = self.db.users.find_one({"email": email.strip().lower()}, {"_id": 0})
        return doc

    # =========================================================================
    # 2. MRI_SCANS COLLECTION CRUD
    # =========================================================================

    def create_mri_scan(self, scan_data: Union[Dict[str, Any], MRIScan]) -> str:
        """Inserts an MRI scan record."""
        if not self.is_connected:
            raise RuntimeError("Database is disconnected")

        if isinstance(scan_data, dict):
            scan = MRIScan.from_dict(scan_data)
        else:
            scan = scan_data
        scan.validate()

        doc = scan.to_dict()
        self.db.mri_scans.insert_one(doc)
        return scan.scan_id

    def get_mri_scan(self, scan_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves an MRI scan with optional user isolation enforcement."""
        if not self.is_connected:
            return None
        query = {"scan_id": scan_id}
        if user_id:
            query["user_id"] = user_id
        return self.db.mri_scans.find_one(query, {"_id": 0})

    def update_scan_status(self, scan_id: str, status: str) -> bool:
        """Updates the processing status of an MRI scan."""
        if not self.is_connected:
            return False
        res = self.db.mri_scans.update_one(
            {"scan_id": scan_id},
            {"$set": {"processing_status": status, "updated_at": datetime.utcnow().isoformat() + 'Z'}}
        )
        return res.modified_count > 0

    def get_user_scans(
        self,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Lists scans for a user with category filtering, search, and pagination.
        Hydrates scans with their latest detection results.
        """
        if not self.is_connected:
            return []

        query: Dict[str, Any] = {}
        if user_id:
            query["user_id"] = user_id

        if search:
            query["$or"] = [
                {"scan_id": {"$regex": search, "$options": "i"}},
                {"filename": {"$regex": search, "$options": "i"}},
                {"patient_id": {"$regex": search, "$options": "i"}}
            ]

        cursor = self.db.mri_scans.find(query, {"_id": 0}).sort("upload_date", DESCENDING).skip(offset).limit(limit)
        scans = list(cursor)

        # Hydrate detection results
        hydrated = []
        for s in scans:
            det = self.get_detection_result(s["scan_id"])
            if det:
                s["predicted_category"] = det.get("predicted_class")
                s["confidence_score"] = det.get("confidence_score")
                s["probabilities"] = det.get("probabilities")
            else:
                s["predicted_category"] = None
                s["confidence_score"] = None
                s["probabilities"] = None

            # Category filter check
            if category and category != 'All':
                if s["predicted_category"] != category:
                    continue
            hydrated.append(s)

        return hydrated

    def delete_mri_scan(self, scan_id: str, user_id: Optional[str] = None) -> bool:
        """
        Deletes a scan and all associated records across the 6 collections,
        as well as associated physical files on disk.
        """
        if not self.is_connected:
            return False

        scan = self.get_mri_scan(scan_id, user_id=user_id)
        if not scan:
            return False

        # Gather files to remove safely
        files_to_remove = [scan.get('original_image_path')]

        enh = self.get_enhancement_result(scan_id)
        if enh:
            files_to_remove.append(enh.get('clahe_image_path'))
            files_to_remove.append(enh.get('autoencoder_image_path'))

        grad = self.get_gradcam_result(scan_id)
        if grad:
            files_to_remove.append(grad.get('heatmap_image_path'))
            files_to_remove.append(grad.get('overlay_image_path'))

        rpt = self.get_report(scan_id, user_id=user_id)
        if rpt:
            files_to_remove.append(rpt.get('pdf_path'))

        for p in files_to_remove:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception as e:
                    logger.warning(f"Could not remove physical file {p}: {e}")

        # Remove from all 5 related collections
        self.db.mri_scans.delete_one({"scan_id": scan_id})
        self.db.enhancement_results.delete_many({"scan_id": scan_id})
        self.db.detection_results.delete_many({"scan_id": scan_id})
        self.db.gradcam_results.delete_many({"scan_id": scan_id})
        self.db.reports.delete_many({"scan_id": scan_id})

        return True

    # =========================================================================
    # 3. ENHANCEMENT_RESULTS COLLECTION CRUD
    # =========================================================================

    def save_enhancement_result(self, enh_data: Union[Dict[str, Any], EnhancementResult]) -> str:
        """Stores enhancement output and updates scan status."""
        if not self.is_connected:
            raise RuntimeError("Database is disconnected")

        if isinstance(enh_data, dict):
            enh = EnhancementResult.from_dict(enh_data)
        else:
            enh = enh_data
        enh.validate()

        doc = enh.to_dict()
        # Upsert by scan_id so re-enhancing updates existing record
        self.db.enhancement_results.update_one(
            {"scan_id": enh.scan_id},
            {"$set": doc},
            upsert=True
        )
        self.update_scan_status(enh.scan_id, 'enhanced')
        return enh.enhancement_id

    def get_enhancement_result(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves enhancement result for a scan."""
        if not self.is_connected:
            return None
        return self.db.enhancement_results.find_one({"scan_id": scan_id}, {"_id": 0})

    # =========================================================================
    # 4. DETECTION_RESULTS COLLECTION CRUD
    # =========================================================================

    def save_detection_result(self, det_data: Union[Dict[str, Any], DetectionResult]) -> str:
        """Stores CNN classification results and updates scan status."""
        if not self.is_connected:
            raise RuntimeError("Database is disconnected")

        if isinstance(det_data, dict):
            det = DetectionResult.from_dict(det_data)
        else:
            det = det_data
        det.validate()

        doc = det.to_dict()
        self.db.detection_results.update_one(
            {"scan_id": det.scan_id},
            {"$set": doc},
            upsert=True
        )
        self.update_scan_status(det.scan_id, 'analyzed')
        return det.detection_id

    def get_detection_result(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves CNN detection result for a scan."""
        if not self.is_connected:
            return None
        return self.db.detection_results.find_one({"scan_id": scan_id}, {"_id": 0})

    # =========================================================================
    # 5. GRADCAM_RESULTS COLLECTION CRUD
    # =========================================================================

    def save_gradcam_result(self, grad_data: Union[Dict[str, Any], GradCAMResult]) -> str:
        """Stores Grad-CAM visual explainability outputs."""
        if not self.is_connected:
            raise RuntimeError("Database is disconnected")

        if isinstance(grad_data, dict):
            grad = GradCAMResult.from_dict(grad_data)
        else:
            grad = grad_data
        grad.validate()

        doc = grad.to_dict()
        self.db.gradcam_results.update_one(
            {"scan_id": grad.scan_id},
            {"$set": doc},
            upsert=True
        )
        return grad.gradcam_id

    def get_gradcam_result(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves Grad-CAM heatmap/overlay for a scan."""
        if not self.is_connected:
            return None
        return self.db.gradcam_results.find_one({"scan_id": scan_id}, {"_id": 0})

    # =========================================================================
    # 6. REPORTS COLLECTION CRUD
    # =========================================================================

    def save_report(self, rpt_data: Union[Dict[str, Any], Report]) -> str:
        """Stores diagnostic PDF report metadata and marks scan completed."""
        if not self.is_connected:
            raise RuntimeError("Database is disconnected")

        if isinstance(rpt_data, dict):
            rpt = Report.from_dict(rpt_data)
        else:
            rpt = rpt_data
        rpt.validate()

        doc = rpt.to_dict()
        self.db.reports.update_one(
            {"scan_id": rpt.scan_id},
            {"$set": doc},
            upsert=True
        )
        self.update_scan_status(rpt.scan_id, 'completed')
        return rpt.report_id

    def get_report(self, scan_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves report metadata with optional user isolation check."""
        if not self.is_connected:
            return None
        query = {"scan_id": scan_id}
        if user_id:
            query["user_id"] = user_id
        return self.db.reports.find_one(query, {"_id": 0})

    def get_user_reports(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves all reports generated for a given user."""
        if not self.is_connected:
            return []
        cursor = self.db.reports.find({"user_id": user_id}, {"_id": 0}).sort("generated_at", DESCENDING).limit(limit)
        return list(cursor)

    # =========================================================================
    # AGGREGATED STUDY VIEW (Joins Scan + Enh + Det + Grad + Report)
    # =========================================================================

    def get_full_study(self, scan_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Combines scan metadata with its OpenCV enhancement, CNN detection, Grad-CAM,
        and PDF report into a unified diagnostic workstation dictionary.
        """
        scan = self.get_mri_scan(scan_id, user_id=user_id)
        if not scan:
            return None

        study = dict(scan)
        study["created_at"] = scan.get("upload_date")
        study["original_path"] = scan.get("original_image_path") or scan.get("original_path")
        study["original_image_path"] = scan.get("original_image_path") or scan.get("original_path")

        # URLs
        filename = scan.get("filename", "")
        saved_filename = os.path.basename(study["original_path"] or "")
        study["original_url"] = f"/uploads/{saved_filename}" if saved_filename else ""

        # Enhancement
        enh = self.get_enhancement_result(scan_id)
        if enh:
            enh_filename = os.path.basename(enh.get("clahe_image_path", ""))
            study["enhanced_url"] = f"/enhanced_images/{enh_filename}" if enh_filename else ""
            study["enhanced_path"] = enh.get("clahe_image_path")
            study["enhancement_params"] = enh.get("parameters")
            study["enhancement_method"] = enh.get("enhancement_method")
        else:
            study["enhanced_url"] = None
            study["enhanced_path"] = None
            study["enhancement_params"] = None

        # Detection
        det = self.get_detection_result(scan_id)
        if det:
            study["predicted_category"] = det.get("predicted_class")
            study["confidence_score"] = det.get("confidence_score")
            study["probabilities"] = det.get("probabilities")
            study["model_name"] = det.get("model_name")
            study["model_version"] = det.get("model_version")
        else:
            study["predicted_category"] = None
            study["confidence_score"] = None
            study["probabilities"] = None

        # Grad-CAM
        grad = self.get_gradcam_result(scan_id)
        if grad:
            gdc_filename = os.path.basename(grad.get("overlay_image_path", ""))
            study["gradcam_url"] = f"/enhanced_images/{gdc_filename}" if gdc_filename else ""
            study["gradcam_path"] = grad.get("overlay_image_path")
            study["heatmap_url"] = f"/enhanced_images/{os.path.basename(grad.get('heatmap_image_path', ''))}"
        else:
            study["gradcam_url"] = None
            study["gradcam_path"] = None

        # Report
        rpt = self.get_report(scan_id, user_id=user_id)
        if rpt:
            pdf_filename = os.path.basename(rpt.get("pdf_path", ""))
            study["report_url"] = f"/reports/{pdf_filename}" if pdf_filename else ""
            study["report_pdf_path"] = rpt.get("pdf_path")
            study["report_summary"] = rpt.get("summary")
        else:
            study["report_url"] = None
            study["report_pdf_path"] = None

        return study

    # =========================================================================
    # DASHBOARD ANALYTICS
    # =========================================================================

    def get_dashboard_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculates aggregate dashboard metrics from MongoDB."""
        if not self.is_connected:
            return {
                "total_scans": 0,
                "scans_by_category": {},
                "average_confidence": 0.0,
                "enhanced_count": 0,
                "recent_scans": [],
                "activity_data": []
            }

        scan_query = {"user_id": user_id} if user_id else {}
        total_scans = self.db.mri_scans.count_documents(scan_query)

        # Scans by category
        categories = ['Glioma', 'Meningioma', 'Pituitary Tumor', 'No Tumor']
        cat_counts = {cat: 0 for cat in categories}
        cat_counts['Pending / Unclassified'] = 0

        # Scan detection results
        all_scans = list(self.db.mri_scans.find(scan_query, {"scan_id": 1, "upload_date": 1, "filename": 1, "patient_id": 1}))
        scan_ids = [s["scan_id"] for s in all_scans]

        confidences = []
        for s in all_scans:
            det = self.db.detection_results.find_one({"scan_id": s["scan_id"]})
            if det and det.get("predicted_class"):
                cat = det["predicted_class"]
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
                if det.get("confidence_score") is not None:
                    confidences.append(float(det["confidence_score"]))
            else:
                cat_counts['Pending / Unclassified'] += 1

        avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
        enhanced_count = self.db.enhancement_results.count_documents({"scan_id": {"$in": scan_ids}}) if scan_ids else 0

        # Recent 5 scans
        recent_scans = []
        recent_cursor = self.db.mri_scans.find(scan_query, {"_id": 0}).sort("upload_date", DESCENDING).limit(5)
        for r in recent_cursor:
            det = self.db.detection_results.find_one({"scan_id": r["scan_id"]})
            recent_scans.append({
                "scan_id": r.get("scan_id"),
                "filename": r.get("filename"),
                "created_at": r.get("upload_date"),
                "predicted_category": det.get("predicted_class") if det else None,
                "confidence_score": det.get("confidence_score") if det else None,
                "patient_id": r.get("patient_id")
            })

        # Activity timeline by date
        date_counts: Dict[str, int] = {}
        for s in all_scans:
            d_str = (s.get("upload_date") or "")[:10]
            if d_str:
                date_counts[d_str] = date_counts.get(d_str, 0) + 1

        activity_data = [{"date": k, "scans": v} for k, v in sorted(date_counts.items())][-14:]

        return {
            "total_scans": total_scans,
            "scans_by_category": cat_counts,
            "average_confidence": avg_conf,
            "enhanced_count": enhanced_count,
            "recent_scans": recent_scans,
            "activity_data": activity_data
        }

    # =========================================================================
    # HEALTH CHECK & DIAGNOSTICS
    # =========================================================================

    def get_health_status(self) -> Dict[str, Any]:
        """Returns database health details with safe masked credentials."""
        status = {
            "status": "connected" if self.is_connected else "disconnected",
            "database_name": self.db_name,
            "engine": "MongoDB Atlas / Server" if (self.is_connected and not self.is_mock) else ("In-Memory PyMongo Resilient Engine" if self.is_mock else "Unavailable"),
            "masked_uri": DatabaseConfig.get_masked_uri(),
            "collections": []
        }
        if self.is_connected and self.db is not None:
            try:
                collections = ["users", "mri_scans", "enhancement_results", "detection_results", "gradcam_results", "reports"]
                stats = {}
                for c in collections:
                    stats[c] = self.db[c].count_documents({})
                status["collections"] = stats
            except Exception as e:
                status["error"] = str(e)
        else:
            status["error"] = self.error_message
        return status

# Global singleton accessor
def get_db_manager() -> DatabaseManager:
    return DatabaseManager()

# =============================================================================
# CONVENIENCE / BACKWARDS-COMPATIBLE API FUNCTIONS
# (Delegates to MongoDB with SQLite dual-sync)
# =============================================================================

import sqlite3
import json

SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brain_tumor.db')

def get_sqlite_conn():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite schema and ensures MongoDB indexes."""
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            original_path TEXT NOT NULL,
            enhanced_path TEXT,
            gradcam_path TEXT,
            created_at TEXT NOT NULL,
            predicted_category TEXT,
            confidence_score REAL,
            probabilities TEXT,
            enhancement_params TEXT,
            report_text TEXT,
            report_pdf_path TEXT,
            dimensions TEXT,
            file_size INTEGER,
            patient_id TEXT,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

    # Trigger MongoDB connection & indexing
    mgr = get_db_manager()
    if mgr.is_connected:
        print("[MongoDB] System ready with 6 collections & indexes initialized.")

def create_scan(scan_data: Dict[str, Any]) -> str:
    """Inserts a new scan into MongoDB mri_scans collection and syncs with SQLite."""
    scan_id = scan_data.get('scan_id')
    filename = scan_data.get('filename')
    original_path = scan_data.get('original_path')
    created_at = scan_data.get('created_at', datetime.utcnow().isoformat())
    dimensions = scan_data.get('dimensions', '')
    file_size = scan_data.get('file_size', 0)
    patient_id = scan_data.get('patient_id', f"PAT-{datetime.now().strftime('%y%m%d%H%M')}")
    user_id = scan_data.get('user_id', 'USR-CLINICIAN-001')
    image_format = scan_data.get('image_format') or (filename.rsplit('.', 1)[1].upper() if filename and '.' in filename else 'JPEG')

    # 1. MongoDB insertion
    mgr = get_db_manager()
    if mgr.is_connected:
        try:
            mongo_scan = MRIScan(
                scan_id=scan_id,
                user_id=user_id,
                original_image_path=original_path,
                image_format=image_format,
                upload_date=created_at,
                processing_status='uploaded',
                filename=filename,
                dimensions=dimensions,
                file_size=file_size,
                patient_id=patient_id
            )
            mgr.create_mri_scan(mongo_scan)
        except Exception as e:
            logger.warning(f"MongoDB create_scan warning: {e}")

    # 2. SQLite dual-sync
    try:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO scans (
                scan_id, filename, original_path, created_at, dimensions, file_size, patient_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (scan_id, filename, original_path, created_at, dimensions, file_size, patient_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"SQLite sync warning: {e}")

    return scan_id

def update_scan(scan_id: str, update_data: Dict[str, Any]):
    """Updates scan and syncs outputs into enhancement_results, detection_results, etc."""
    mgr = get_db_manager()
    if mgr.is_connected:
        try:
            if 'enhanced_path' in update_data and update_data['enhanced_path']:
                enh = EnhancementResult(
                    scan_id=scan_id,
                    clahe_image_path=update_data['enhanced_path'],
                    enhancement_method='OpenCV CLAHE + Bilateral Filtering',
                    parameters=update_data.get('enhancement_params', {})
                )
                mgr.save_enhancement_result(enh)

            if 'predicted_category' in update_data and update_data['predicted_category']:
                det = DetectionResult(
                    scan_id=scan_id,
                    predicted_class=update_data['predicted_category'],
                    confidence_score=update_data.get('confidence_score', 0.0),
                    probabilities=update_data.get('probabilities', {})
                )
                mgr.save_detection_result(det)

            if 'gradcam_path' in update_data and update_data['gradcam_path']:
                grad = GradCAMResult(
                    scan_id=scan_id,
                    heatmap_image_path=update_data['gradcam_path'],
                    overlay_image_path=update_data['gradcam_path']
                )
                mgr.save_gradcam_result(grad)

            if 'report_pdf_path' in update_data and update_data['report_pdf_path']:
                scan = mgr.get_mri_scan(scan_id)
                user_id = scan.get('user_id', 'USR-CLINICIAN-001') if scan else 'USR-CLINICIAN-001'
                rpt = Report(
                    scan_id=scan_id,
                    user_id=user_id,
                    pdf_path=update_data['report_pdf_path'],
                    summary={"text": update_data.get('report_text', '')}
                )
                mgr.save_report(rpt)
        except Exception as e:
            logger.warning(f"MongoDB update_scan warning: {e}")

    # SQLite sync
    try:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        fields = []
        values = []
        for k, v in update_data.items():
            if k in ['enhanced_path', 'gradcam_path', 'predicted_category', 'confidence_score',
                     'probabilities', 'enhancement_params', 'report_text', 'report_pdf_path',
                     'patient_id', 'notes']:
                fields.append(f"{k} = ?")
                if isinstance(v, (dict, list)):
                    values.append(json.dumps(v))
                else:
                    values.append(v)
        if fields:
            values.append(scan_id)
            cursor.execute(f"UPDATE scans SET {', '.join(fields)} WHERE scan_id = ?", values)
            conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"SQLite update warning: {e}")

def get_scan(scan_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves full study from MongoDB with SQLite fallback."""
    mgr = get_db_manager()
    if mgr.is_connected:
        try:
            study = mgr.get_full_study(scan_id, user_id=user_id)
            if study:
                return study
        except Exception as e:
            logger.warning(f"MongoDB get_scan warning: {e}")

    # SQLite fallback
    try:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scans WHERE scan_id = ?", (scan_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        d = dict(row)
        for field in ['probabilities', 'enhancement_params']:
            if d.get(field):
                try:
                    d[field] = json.loads(d[field])
                except Exception:
                    pass
        return d
    except Exception:
        return None

def get_all_scans(user_id=None, category=None, search=None, limit=100, offset=0) -> List[Dict[str, Any]]:
    """Retrieves list of scans from MongoDB with SQLite fallback."""
    mgr = get_db_manager()
    if mgr.is_connected:
        try:
            mongo_scans = mgr.get_user_scans(user_id=user_id, category=category, search=search, limit=limit, offset=offset)
            if mongo_scans:
                results = []
                for s in mongo_scans:
                    d = dict(s)
                    d["created_at"] = s.get("upload_date")
                    saved_fn = os.path.basename(s.get("original_image_path", ""))
                    d["original_url"] = f"/uploads/{saved_fn}" if saved_fn else ""
                    enh = mgr.get_enhancement_result(s["scan_id"])
                    if enh:
                        enh_fn = os.path.basename(enh.get("clahe_image_path", ""))
                        d["enhanced_url"] = f"/enhanced_images/{enh_fn}" if enh_fn else ""
                        d["enhanced_path"] = enh.get("clahe_image_path")
                    grad = mgr.get_gradcam_result(s["scan_id"])
                    if grad:
                        grad_fn = os.path.basename(grad.get("overlay_image_path", ""))
                        d["gradcam_url"] = f"/enhanced_images/{grad_fn}" if grad_fn else ""
                        d["gradcam_path"] = grad.get("overlay_image_path")
                    results.append(d)
                return results
        except Exception as e:
            logger.warning(f"MongoDB get_all_scans warning: {e}")

    # SQLite fallback
    try:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        query = "SELECT * FROM scans WHERE 1=1"
        params = []
        if category and category != 'All':
            query += " AND predicted_category = ?"
            params.append(category)
        if search:
            query += " AND (scan_id LIKE ? OR filename LIKE ? OR patient_id LIKE ?)"
            like_s = f"%{search}%"
            params.extend([like_s, like_s, like_s])
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        results = []
        for row in rows:
            d = dict(row)
            for f in ['probabilities', 'enhancement_params']:
                if d.get(f):
                    try:
                        d[f] = json.loads(d[f])
                    except Exception:
                        pass
            results.append(d)
        return results
    except Exception:
        return []

def delete_scan(scan_id: str, user_id: Optional[str] = None) -> bool:
    """Deletes scan from MongoDB and SQLite."""
    mongo_deleted = False
    mgr = get_db_manager()
    if mgr.is_connected:
        try:
            mongo_deleted = mgr.delete_mri_scan(scan_id, user_id=user_id)
        except Exception as e:
            logger.warning(f"MongoDB delete warning: {e}")

    sqlite_deleted = False
    try:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT original_path, enhanced_path, gradcam_path, report_pdf_path FROM scans WHERE scan_id = ?", (scan_id,))
        row = cursor.fetchone()
        if row:
            for p in row:
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
            cursor.execute("DELETE FROM scans WHERE scan_id = ?", (scan_id,))
            conn.commit()
            sqlite_deleted = cursor.rowcount > 0
        conn.close()
    except Exception:
        pass

    return mongo_deleted or sqlite_deleted

def get_dashboard_stats(user_id: Optional[str] = None) -> Dict[str, Any]:
    """Calculates dashboard analytics from MongoDB with SQLite fallback."""
    mgr = get_db_manager()
    if mgr.is_connected:
        try:
            stats = mgr.get_dashboard_statistics(user_id=user_id)
            if stats and stats.get("total_scans", 0) > 0:
                return stats
        except Exception as e:
            logger.warning(f"MongoDB stats warning: {e}")

    # SQLite fallback
    try:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM scans")
        total_scans = cursor.fetchone()[0]

        cat_counts = {'Glioma': 0, 'Meningioma': 0, 'Pituitary Tumor': 0, 'No Tumor': 0, 'Pending / Unclassified': 0}
        cursor.execute("SELECT predicted_category, COUNT(*) FROM scans GROUP BY predicted_category")
        for cat, cnt in cursor.fetchall():
            if cat in cat_counts:
                cat_counts[cat] = cnt
            elif cat:
                cat_counts[cat] = cnt
            else:
                cat_counts['Pending / Unclassified'] += cnt

        cursor.execute("SELECT AVG(confidence_score) FROM scans WHERE confidence_score IS NOT NULL")
        avg_r = cursor.fetchone()
        avg_conf = round(avg_r[0], 2) if avg_r and avg_r[0] is not None else 0.0

        cursor.execute("SELECT COUNT(*) FROM scans WHERE enhanced_path IS NOT NULL")
        enhanced_count = cursor.fetchone()[0]

        cursor.execute("SELECT scan_id, filename, created_at, predicted_category, confidence_score, patient_id FROM scans ORDER BY created_at DESC LIMIT 5")
        recent = [dict(r) for r in cursor.fetchall()]

        cursor.execute("""
            SELECT substr(created_at, 1, 10) as scan_date, COUNT(*) as count 
            FROM scans 
            GROUP BY scan_date 
            ORDER BY scan_date ASC 
            LIMIT 14
        """)
        timeline = [{"date": r[0], "scans": r[1]} for r in cursor.fetchall()]
        conn.close()

        return {
            "total_scans": total_scans,
            "scans_by_category": cat_counts,
            "average_confidence": avg_conf,
            "enhanced_count": enhanced_count,
            "recent_scans": recent,
            "activity_data": timeline
        }
    except Exception:
        return {
            "total_scans": 0,
            "scans_by_category": {},
            "average_confidence": 0.0,
            "enhanced_count": 0,
            "recent_scans": [],
            "activity_data": []
        }

# Backwards compatibility alias
import sys
sys.modules['database.db'] = sys.modules[__name__]

