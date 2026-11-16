import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

from database.db import init_db
from routes.api_routes import api_bp

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173", "*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Origin"]
    }})
    
    # Initialize SQLite schema
    with app.app_context():
        init_db()
        print("SQLite Database initialized at backend/database/brain_tumor.db")
        
    # Register API blueprint
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    uploads_dir = os.path.join(base_dir, 'uploads')
    enhanced_dir = os.path.join(base_dir, 'enhanced_images')
    reports_dir = os.path.join(base_dir, 'reports')
    samples_dir = os.path.join(base_dir, 'sample_mris')
    
    for d in [uploads_dir, enhanced_dir, reports_dir, samples_dir]:
        os.makedirs(d, exist_ok=True)
        
    # Static asset endpoints
    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        return send_from_directory(uploads_dir, filename)

    @app.route('/enhanced_images/<path:filename>')
    def serve_enhanced(filename):
        return send_from_directory(enhanced_dir, filename)

    @app.route('/reports/<path:filename>')
    def serve_reports(filename):
        return send_from_directory(reports_dir, filename)

    @app.route('/sample_mris/<path:filename>')
    def serve_samples(filename):
        return send_from_directory(samples_dir, filename)

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
            "frontend_url": "http://localhost:3000",
            "health_check": "/api/health"
        }), 200

    @app.route('/health')
    @app.route('/api/health')
    def health():
        return jsonify({"status": "success", "message": "Backend is running"}), 200

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting NeuroScan-AI Backend Server on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
