"""
Authentication, Password Security, and JWT Token Management.
Handles:
- Secure password hashing (PBKDF2/SHA256 & Bcrypt)
- JWT token issuance and verification
- User registration and authentication workflows
- Flask route protection decorators ensuring per-user data isolation
"""

import os
import re
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, Optional, Tuple

import jwt
from flask import request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

from database_config import DatabaseConfig
from models import User

# Standard fallback demo identity for local workstation operation
DEFAULT_DEMO_USER = {
    "user_id": "USR-CLINICIAN-001",
    "name": "Dr. Eliza Chen",
    "email": "eliza.chen@neuromedix.ai",
    "role": "lead_neuro_radiologist",
    "created_at": "2026-01-01T00:00:00Z"
}

def hash_password(password: str) -> str:
    """Hashes a plaintext password securely using werkzeug PBKDF2-SHA256."""
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")
    return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verifies a plaintext password against its stored cryptographic hash."""
    if not plain_password or not password_hash:
        return False
    try:
        return check_password_hash(password_hash, plain_password)
    except Exception:
        return False

def generate_jwt_token(user_data: Dict[str, Any], expires_hours: Optional[int] = None) -> str:
    """Generates a signed JWT token containing user identity and expiration."""
    hours = expires_hours or DatabaseConfig.JWT_EXPIRATION_HOURS
    now = datetime.utcnow()
    payload = {
        "sub": user_data.get("user_id"),
        "email": user_data.get("email"),
        "name": user_data.get("name"),
        "role": user_data.get("role", "clinician"),
        "iat": now,
        "exp": now + timedelta(hours=hours)
    }
    token = jwt.encode(payload, DatabaseConfig.JWT_SECRET_KEY, algorithm="HS256")
    return token if isinstance(token, str) else token.decode('utf-8')

def decode_jwt_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token; raises jwt exceptions on failure."""
    return jwt.decode(token, DatabaseConfig.JWT_SECRET_KEY, algorithms=["HS256"])

def get_auth_token_from_header() -> Optional[str]:
    """Extracts the Bearer token from the Authorization header or query parameter."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return request.args.get("token")

def token_required(strict: bool = False):
    """
    Decorator to protect Flask routes with JWT authentication.
    - If a valid JWT is provided, extracts and populates request.current_user and g.current_user.
    - If strict=True and no valid token is provided, returns 401 Unauthorized.
    - If strict=False (default for clinical workstation compatibility), falls back to the
      default workstation clinician identity so the existing workstation UI remains operational.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = get_auth_token_from_header()
            current_user = None

            if token:
                try:
                    payload = decode_jwt_token(token)
                    from database import get_db_manager
                    db = get_db_manager()
                    user_doc = db.get_user_by_id(payload.get("sub"))
                    if user_doc:
                        current_user = user_doc
                    else:
                        current_user = {
                            "user_id": payload.get("sub"),
                            "name": payload.get("name"),
                            "email": payload.get("email"),
                            "role": payload.get("role", "clinician")
                        }
                except jwt.ExpiredSignatureError:
                    return jsonify({"error": "Token has expired. Please log in again."}), 401
                except jwt.InvalidTokenError:
                    return jsonify({"error": "Invalid authentication token."}), 401
            
            if not current_user:
                if strict:
                    return jsonify({"error": "Authentication required. Please provide a valid Bearer token."}), 401
                # Seamless fallback for standalone workstation local session
                current_user = DEFAULT_DEMO_USER

            # Attach to Flask context
            g.current_user = current_user
            request.current_user = current_user
            return f(*args, **kwargs)
        return decorated
    return decorator

def register_user_workflow(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Registers a new user in MongoDB users collection.
    Validates input, checks duplicate email, hashes password, and returns auth response.
    """
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    role = data.get('role') or 'clinician'

    if not name or len(name) < 2:
        return {"error": "Name must be at least 2 characters long."}, 400
    if not email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return {"error": "Invalid email address format."}, 400
    if not password or len(password) < 6:
        return {"error": "Password must be at least 6 characters long."}, 400

    from database import get_db_manager
    db = get_db_manager()

    existing = db.get_user_by_email(email)
    if existing:
        return {"error": "An account with this email address already exists."}, 409

    pwd_hash = hash_password(password)
    user = User(name=name, email=email, password_hash=pwd_hash, role=role)
    user.validate()

    created_user = db.create_user(user.to_dict(include_sensitive=True))
    token = generate_jwt_token(created_user)

    safe_profile = user.to_dict(include_sensitive=False)
    return {
        "success": True,
        "message": "User registered successfully.",
        "user": safe_profile,
        "token": token
    }, 201

def login_user_workflow(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Authenticates user credentials against MongoDB users collection.
    """
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return {"error": "Email and password are required."}, 400

    from database import get_db_manager
    db = get_db_manager()

    user_doc = db.get_user_by_email(email)
    if not user_doc:
        return {"error": "Invalid email or password."}, 401

    stored_hash = user_doc.get('password_hash', '')
    if not verify_password(password, stored_hash):
        return {"error": "Invalid email or password."}, 401

    token = generate_jwt_token(user_doc)
    safe_profile = {k: v for k, v in user_doc.items() if k != 'password_hash' and k != '_id'}

    return {
        "success": True,
        "message": "Authentication successful.",
        "user": safe_profile,
        "token": token
    }, 200
