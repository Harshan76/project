import sqlite3
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger("brainsight.db")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brain_tumor.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite schema and MongoDB connection & indexes."""
    # 1. Initialize SQLite schema
    conn = get_db_connection()
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

    # 2. Initialize MongoDB PyMongo connection & collections
    try:
        from database import get_db_manager
        db_mgr = get_db_manager()
        if db_mgr.is_connected:
            logger.info("MongoDB initialized with 6 collections and indexes.")
    except Exception as e:
        logger.warning(f"MongoDB initialization notice: {e}")

def create_scan(scan_data):
    """Creates scan in both MongoDB mri_scans collection and SQLite."""
    scan_id = scan_data.get('scan_id')
    filename = scan_data.get('filename')
    original_path = scan_data.get('original_path')
    created_at = scan_data.get('created_at', datetime.utcnow().isoformat())
    dimensions = scan_data.get('dimensions', '')
    file_size = scan_data.get('file_size', 0)
    patient_id = scan_data.get('patient_id', f"PAT-{datetime.now().strftime('%y%m%d%H%M')}")
    user_id = scan_data.get('user_id', 'USR-CLINICIAN-001')
    image_format = scan_data.get('image_format') or (filename.rsplit('.', 1)[1].upper() if '.' in filename else 'JPEG')

    # 1. Save to MongoDB (mri_scans collection)
    try:
        from database import get_db_manager
        from models import MRIScan
        db_mgr = get_db_manager()
        if db_mgr.is_connected:
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
            db_mgr.create_mri_scan(mongo_scan)
    except Exception as e:
        logger.warning(f"MongoDB create_scan warning: {e}")

    # 2. Save to SQLite for backwards-compatibility
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scans (
            scan_id, filename, original_path, created_at, dimensions, file_size, patient_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (scan_id, filename, original_path, created_at, dimensions, file_size, patient_id))
    conn.commit()
    conn.close()
    return scan_id

def update_scan(scan_id, update_data):
    """Updates scan and synchronizes results across MongoDB collections."""
    # 1. Update MongoDB collections
    try:
        from database import get_db_manager
        from models import EnhancementResult, DetectionResult, GradCAMResult, Report
        db_mgr = get_db_manager()

        if db_mgr.is_connected:
            # Enhancement
            if 'enhanced_path' in update_data and update_data['enhanced_path']:
                enh = EnhancementResult(
                    scan_id=scan_id,
                    clahe_image_path=update_data['enhanced_path'],
                    enhancement_method='OpenCV CLAHE + Bilateral Filtering',
                    parameters=update_data.get('enhancement_params', {})
                )
                db_mgr.save_enhancement_result(enh)

            # Detection
            if 'predicted_category' in update_data and update_data['predicted_category']:
                det = DetectionResult(
                    scan_id=scan_id,
                    predicted_class=update_data['predicted_category'],
                    confidence_score=update_data.get('confidence_score', 0.0),
                    probabilities=update_data.get('probabilities', {})
                )
                db_mgr.save_detection_result(det)

            # Grad-CAM
            if 'gradcam_path' in update_data and update_data['gradcam_path']:
                grad = GradCAMResult(
                    scan_id=scan_id,
                    heatmap_image_path=update_data['gradcam_path'],
                    overlay_image_path=update_data['gradcam_path']
                )
                db_mgr.save_gradcam_result(grad)

            # Reports
            if 'report_pdf_path' in update_data and update_data['report_pdf_path']:
                scan = db_mgr.get_mri_scan(scan_id)
                user_id = scan.get('user_id', 'USR-CLINICIAN-001') if scan else 'USR-CLINICIAN-001'
                rpt = Report(
                    scan_id=scan_id,
                    user_id=user_id,
                    pdf_path=update_data['report_pdf_path'],
                    summary={"text": update_data.get('report_text', '')}
                )
                db_mgr.save_report(rpt)
    except Exception as e:
        logger.warning(f"MongoDB update_scan warning: {e}")

    # 2. Update SQLite
    conn = get_db_connection()
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
        query = f"UPDATE scans SET {', '.join(fields)} WHERE scan_id = ?"
        cursor.execute(query, values)
        conn.commit()
    conn.close()

def get_scan(scan_id, user_id=None):
    """Retrieves full scan study from MongoDB with SQLite fallback."""
    # 1. Try MongoDB first
    try:
        from database import get_db_manager
        db_mgr = get_db_manager()
        if db_mgr.is_connected:
            study = db_mgr.get_full_study(scan_id, user_id=user_id)
            if study:
                return study
    except Exception as e:
        logger.warning(f"MongoDB get_scan warning: {e}")

    # 2. SQLite fallback
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scans WHERE scan_id = ?", (scan_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    
    d = dict(row)
    if d.get('probabilities'):
        try:
            d['probabilities'] = json.loads(d['probabilities'])
        except Exception:
            pass
    if d.get('enhancement_params'):
        try:
            d['enhancement_params'] = json.loads(d['enhancement_params'])
        except Exception:
            pass
    return d

def get_all_scans(user_id=None, category=None, search=None, limit=100, offset=0):
    """Retrieves all scans matching filters from MongoDB with SQLite fallback."""
    # 1. Try MongoDB first
    try:
        from database import get_db_manager
        db_mgr = get_db_manager()
        if db_mgr.is_connected:
            mongo_scans = db_mgr.get_user_scans(user_id=user_id, category=category, search=search, limit=limit, offset=offset)
            if mongo_scans:
                results = []
                for s in mongo_scans:
                    d = dict(s)
                    d["created_at"] = s.get("upload_date")
                    saved_fn = os.path.basename(s.get("original_image_path", ""))
                    d["original_url"] = f"/uploads/{saved_fn}" if saved_fn else ""
                    enh = db_mgr.get_enhancement_result(s["scan_id"])
                    if enh:
                        enh_fn = os.path.basename(enh.get("clahe_image_path", ""))
                        d["enhanced_url"] = f"/enhanced_images/{enh_fn}" if enh_fn else ""
                        d["enhanced_path"] = enh.get("clahe_image_path")
                    grad = db_mgr.get_gradcam_result(s["scan_id"])
                    if grad:
                        grad_fn = os.path.basename(grad.get("overlay_image_path", ""))
                        d["gradcam_url"] = f"/enhanced_images/{grad_fn}" if grad_fn else ""
                        d["gradcam_path"] = grad.get("overlay_image_path")
                    results.append(d)
                return results
    except Exception as e:
        logger.warning(f"MongoDB get_all_scans warning: {e}")

    # 2. SQLite fallback
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM scans WHERE 1=1"
    params = []
    
    if category and category != 'All':
        query += " AND predicted_category = ?"
        params.append(category)
        
    if search:
        query += " AND (scan_id LIKE ? OR filename LIKE ? OR patient_id LIKE ?)"
        like_search = f"%{search}%"
        params.extend([like_search, like_search, like_search])
        
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        d = dict(row)
        if d.get('probabilities'):
            try:
                d['probabilities'] = json.loads(d['probabilities'])
            except Exception:
                pass
        if d.get('enhancement_params'):
            try:
                d['enhancement_params'] = json.loads(d['enhancement_params'])
            except Exception:
                pass
        results.append(d)
    return results

def delete_scan(scan_id, user_id=None):
    """Deletes scan from MongoDB and SQLite."""
    # 1. MongoDB delete
    mongo_deleted = False
    try:
        from database import get_db_manager
        db_mgr = get_db_manager()
        if db_mgr.is_connected:
            mongo_deleted = db_mgr.delete_mri_scan(scan_id, user_id=user_id)
    except Exception as e:
        logger.warning(f"MongoDB delete_scan warning: {e}")

    # 2. SQLite delete
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT original_path, enhanced_path, gradcam_path, report_pdf_path FROM scans WHERE scan_id = ?", (scan_id,))
    row = cursor.fetchone()
    
    if row:
        for path in row:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
        cursor.execute("DELETE FROM scans WHERE scan_id = ?", (scan_id,))
        conn.commit()
        sqlite_deleted = cursor.rowcount > 0
    else:
        sqlite_deleted = False
        
    conn.close()
    return mongo_deleted or sqlite_deleted

def get_dashboard_stats(user_id=None):
    """Calculates dashboard analytics from MongoDB with SQLite fallback."""
    # 1. MongoDB stats
    try:
        from database import get_db_manager
        db_mgr = get_db_manager()
        if db_mgr.is_connected:
            stats = db_mgr.get_dashboard_statistics(user_id=user_id)
            if stats and stats.get("total_scans", 0) > 0:
                return stats
    except Exception as e:
        logger.warning(f"MongoDB get_dashboard_stats warning: {e}")

    # 2. SQLite fallback
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM scans")
    total_scans = cursor.fetchone()[0]
    
    categories = ['Glioma', 'Meningioma', 'Pituitary Tumor', 'No Tumor']
    cat_counts = {cat: 0 for cat in categories}
    cat_counts['Pending / Unclassified'] = 0
    
    cursor.execute("SELECT predicted_category, COUNT(*) FROM scans GROUP BY predicted_category")
    for cat, count in cursor.fetchall():
        if cat in cat_counts:
            cat_counts[cat] = count
        elif cat:
            cat_counts[cat] = count
        else:
            cat_counts['Pending / Unclassified'] += count
            
    cursor.execute("SELECT AVG(confidence_score) FROM scans WHERE confidence_score IS NOT NULL")
    avg_conf_row = cursor.fetchone()
    avg_confidence = round(avg_conf_row[0], 2) if avg_conf_row and avg_conf_row[0] is not None else 0.0
    
    cursor.execute("SELECT COUNT(*) FROM scans WHERE enhanced_path IS NOT NULL")
    enhanced_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT scan_id, filename, created_at, predicted_category, confidence_score, patient_id FROM scans ORDER BY created_at DESC LIMIT 5")
    recent_scans = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("""
        SELECT substr(created_at, 1, 10) as scan_date, COUNT(*) as count 
        FROM scans 
        GROUP BY scan_date 
        ORDER BY scan_date ASC 
        LIMIT 14
    """)
    activity_data = [{"date": row[0], "scans": row[1]} for row in cursor.fetchall()]
    conn.close()
    
    return {
        "total_scans": total_scans,
        "scans_by_category": cat_counts,
        "average_confidence": avg_confidence,
        "enhanced_count": enhanced_count,
        "recent_scans": recent_scans,
        "activity_data": activity_data
    }
