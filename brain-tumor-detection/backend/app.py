import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

from database import init_db
from routes.api_routes import api_bp

def create_app():
    app = Flask(__name__)
    
    # -------------------------------------------------------------------------
    # 1. Configurable Storage Directories (Render Persistent Disk / Local)
    # -------------------------------------------------------------------------
    base_dir = os.path.dirname(os.path.abspath(__file__))
    storage_base = os.getenv('STORAGE_DIR', base_dir)
    
    uploads_dir = os.getenv('UPLOADS_DIR', os.path.join(storage_base, 'uploads'))
    enhanced_dir = os.getenv('ENHANCED_DIR', os.path.join(storage_base, 'enhanced_images'))
    reports_dir = os.getenv('REPORTS_DIR', os.path.join(storage_base, 'reports'))
    samples_dir = os.getenv('SAMPLES_DIR', os.path.join(base_dir, 'sample_mris'))
    
    for d in [uploads_dir, enhanced_dir, reports_dir, samples_dir]:
        os.makedirs(d, exist_ok=True)
        
    app.config['UPLOAD_FOLDER'] = uploads_dir
    app.config['ENHANCED_FOLDER'] = enhanced_dir
    app.config['REPORTS_FOLDER'] = reports_dir
    app.config['SAMPLES_FOLDER'] = samples_dir

    # -------------------------------------------------------------------------
    # 2. CORS Configuration for Vercel Frontend & Local Development
    # -------------------------------------------------------------------------
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]
    # Allow Vercel production and preview URLs via FRONTEND_URL environment variable
    custom_origins = os.getenv('FRONTEND_URL') or os.getenv('CORS_ORIGIN') or os.getenv('ALLOWED_ORIGINS')
    if custom_origins:
        for orig in custom_origins.split(','):
            cleaned = orig.strip().rstrip('/')
            if cleaned and cleaned not in allowed_origins:
                allowed_origins.append(cleaned)
        cors_origins = allowed_origins
    else:
        # Default to allowing any origin in development/staging
        cors_origins = "*"

    CORS(app, resources={r"/*": {
        "origins": cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Origin", "X-Requested-With"]
    }})
    
    # -------------------------------------------------------------------------
    # 3. Database Initialization (MongoDB + SQLite dual-engine)
    # -------------------------------------------------------------------------
    with app.app_context():
        try:
            init_db()
        except Exception as e:
            print(f"[Warning] Non-fatal database initialization notice: {e}")
        
    # -------------------------------------------------------------------------
    # 4. Blueprint Registration
    # -------------------------------------------------------------------------
    app.register_blueprint(api_bp, url_prefix='/api')
        
    # -------------------------------------------------------------------------
    # 5. Static Asset Endpoints (Configurable Storage)
    # -------------------------------------------------------------------------
    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/enhanced_images/<path:filename>')
    def serve_enhanced(filename):
        return send_from_directory(app.config['ENHANCED_FOLDER'], filename)

    @app.route('/reports/<path:filename>')
    def serve_reports(filename):
        return send_from_directory(app.config['REPORTS_FOLDER'], filename)

    @app.route('/sample_mris/<path:filename>')
    def serve_samples(filename):
        return send_from_directory(app.config['SAMPLES_FOLDER'], filename)

    frontend_dist = os.path.abspath(os.path.join(base_dir, '..', 'frontend', 'dist'))

    @app.route('/assets/<path:filename>')
    def serve_frontend_assets(filename):
        assets_dir = os.path.join(frontend_dist, 'assets')
        if os.path.exists(os.path.join(assets_dir, filename)):
            return send_from_directory(assets_dir, filename)
        return jsonify({"error": "Asset not found"}), 404

    @app.route('/')
    def index():
        if os.path.exists(os.path.join(frontend_dist, 'index.html')):
            return send_from_directory(frontend_dist, 'index.html')
        return jsonify({
            "status": "success",
            "message": "Brain Tumor Detection Backend is running.",
            "service": "Generative AI-Assisted Brain Tumor Detection API",
            "health_check": "/api/health"
        }), 200

    @app.route('/health')
    @app.route('/api/health')
    def health():
        return jsonify({
            "status": "success",
            "message": "Backend is running",
            "service": "BrainSight AI Backend"
        }), 200

    return app

# Module-level application instance for Gunicorn WSGI: `gunicorn app:app`
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    is_debug = os.environ.get('FLASK_DEBUG', 'false').lower() in ('true', '1')
    print(f"Starting NeuroScan-AI Backend Server on http://0.0.0.0:{port} (Debug: {is_debug})")
    app.run(host='0.0.0.0', port=port, debug=is_debug)
