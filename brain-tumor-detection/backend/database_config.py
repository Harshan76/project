"""
Database and Application Configuration for Brain Tumor Detection System.
Handles environment variables, MongoDB URI parsing, JWT secrets, and storage paths.
Never exposes credentials to frontend clients.
"""

import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env if present
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

class DatabaseConfig:
    """Central configuration for MongoDB and Storage."""
    
    # MongoDB Connection
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'brain_tumor_detection')
    
    # Connection Pool and Timeout Settings (ms)
    MONGODB_CONNECT_TIMEOUT_MS = int(os.getenv('MONGODB_CONNECT_TIMEOUT_MS', 4000))
    MONGODB_SERVER_SELECTION_TIMEOUT_MS = int(os.getenv('MONGODB_SERVER_SELECTION_TIMEOUT_MS', 4000))
    MONGODB_SOCKET_TIMEOUT_MS = int(os.getenv('MONGODB_SOCKET_TIMEOUT_MS', 5000))
    MONGODB_MAX_POOL_SIZE = int(os.getenv('MONGODB_MAX_POOL_SIZE', 50))
    
    # Auth & JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'brainsight-neuro-oncology-secure-secret-key-2026')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))
    BCRYPT_ROUNDS = int(os.getenv('BCRYPT_ROUNDS', 12))
    
    # File Storage Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
    ENHANCED_DIR = os.path.join(BASE_DIR, 'enhanced_images')
    REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
    SAMPLES_DIR = os.path.join(BASE_DIR, 'sample_mris')

    # Allow in-memory mock fallback when local/atlas server is not reachable
    ALLOW_MOCK_FALLBACK = os.getenv('ALLOW_MOCK_FALLBACK', 'true').lower() in ('1', 'true', 'yes')

    @classmethod
    def get_masked_uri(cls) -> str:
        """
        Returns a sanitized connection string with credentials replaced by asterisks.
        Guarantees that database passwords are never printed to logs or exposed via APIs.
        """
        uri = cls.MONGODB_URI
        if not uri:
            return ""
        try:
            if '@' in uri:
                prefix, host_part = uri.split('@', 1)
                scheme_user = prefix.split(':', 2)
                if len(scheme_user) >= 3:
                    scheme = scheme_user[0]
                    user = scheme_user[1].replace('//', '')
                    return f"{scheme}://{user}:*****@{host_part}"
                elif len(scheme_user) == 2:
                    return f"{scheme_user[0]}:*****@{host_part}"
            return uri
        except Exception:
            return "mongodb://*****:*****@masked-host"

    @classmethod
    def ensure_storage_dirs(cls):
        """Ensures all necessary asset storage directories exist."""
        for d in [cls.UPLOADS_DIR, cls.ENHANCED_DIR, cls.REPORTS_DIR, cls.SAMPLES_DIR]:
            os.makedirs(d, exist_ok=True)
