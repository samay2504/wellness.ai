"""
Authentication module for Wellness at Work backend
Handles JWT tokens, password hashing, OAuth integration, and security
"""

import os
import jwt
import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
from flask import request, jsonify, current_app
from flask_sqlalchemy import SQLAlchemy
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
import requests as http_requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from models import db, User, AuditLog

logger = logging.getLogger(__name__)


class AuthManager:
    """Main authentication manager for the backend"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the auth manager with Flask app"""
        self.app = app
        self.secret_key = app.config.get('SECRET_KEY', os.environ.get('SECRET_KEY', 'dev-secret-key'))
        self.jwt_expiration = app.config.get('JWT_EXPIRATION_HOURS', 24)
        self.google_client_id = app.config.get('GOOGLE_CLIENT_ID')
        self.google_client_secret = app.config.get('GOOGLE_CLIENT_SECRET')
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_token(self, user_id: int, email: str) -> str:
        """Generate a JWT token for a user"""
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiration),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def generate_refresh_token(self, user_id: int) -> str:
        """Generate a refresh token for a user"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=30),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def get_user_from_token(self, token: str) -> Optional[User]:
        """Get user from JWT token"""
        payload = self.verify_token(token)
        if payload and payload.get('type') == 'access':
            return User.query.get(payload['user_id'])
        return None
    
    def log_audit_event(self, user_id: Optional[int], action: str, success: bool = True, 
                       details: Optional[str] = None):
        """Log an audit event"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource=request.endpoint,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                success=success,
                details=details
            )
            db.session.add(audit_log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    def register_user(self, email: str, password: str, name: str = None) -> Optional[User]:
        """Register a new user"""
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return None
            
            # Create new user
            hashed_password = self.hash_password(password)
            user = User(
                email=email,
                name=name,
                password_hash=hashed_password,
                consent=True  # User consents by registering
            )
            
            db.session.add(user)
            db.session.commit()
            
            # Log audit event
            self.log_audit_event(user.id, 'user_registration', True)
            
            return user
        except Exception as e:
            logger.error(f"Failed to register user: {e}")
            db.session.rollback()
            return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        try:
            user = User.query.filter_by(email=email).first()
            if user and self.verify_password(password, user.password_hash):
                # Log successful login
                self.log_audit_event(user.id, 'login', True)
                return user
            else:
                # Log failed login attempt
                self.log_audit_event(None, 'login', False, f"Failed login attempt for email: {email}")
                return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def authenticate_google_user(self, id_token_str: str) -> Optional[User]:
        """Authenticate a user with Google ID token"""
        try:
            # Verify the ID token
            idinfo = id_token.verify_oauth2_token(
                id_token_str, 
                requests.Request(), 
                self.google_client_id
            )
            
            # Extract user information
            google_user_id = idinfo['sub']
            email = idinfo['email']
            name = idinfo.get('name', '')
            
            # Check if user exists
            user = User.query.filter_by(email=email).first()
            
            if not user:
                # Create new user
                user = User(
                    email=email,
                    name=name,
                    password_hash='',  # No password for OAuth users
                    consent=True
                )
                db.session.add(user)
                db.session.commit()
                
                # Log audit event
                self.log_audit_event(user.id, 'user_registration_oauth', True, 'Google OAuth')
            
            # Log successful login
            self.log_audit_event(user.id, 'login_oauth', True, 'Google OAuth')
            
            return user
        except Exception as e:
            logger.error(f"Google OAuth authentication error: {e}")
            return None
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            # Verify current password
            if not self.verify_password(current_password, user.password_hash):
                return False
            
            # Hash new password
            new_hashed_password = self.hash_password(new_password)
            user.password_hash = new_hashed_password
            user.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Log audit event
            self.log_audit_event(user_id, 'password_change', True)
            
            return True
        except Exception as e:
            logger.error(f"Password change error: {e}")
            db.session.rollback()
            return False
    
    def reset_password_request(self, email: str) -> bool:
        """Request password reset (sends email)"""
        try:
            user = User.query.filter_by(email=email).first()
            if not user:
                return False
            
            # Generate reset token
            reset_token = self.generate_reset_token(user.id)
            
            # Store reset token (in production, use Redis or database)
            # For now, we'll just log it
            logger.info(f"Password reset token for {email}: {reset_token}")
            
            # Log audit event
            self.log_audit_event(user.id, 'password_reset_request', True)
            
            return True
        except Exception as e:
            logger.error(f"Password reset request error: {e}")
            return False
    
    def generate_reset_token(self, user_id: int) -> str:
        """Generate a password reset token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
            'type': 'reset'
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def reset_password(self, reset_token: str, new_password: str) -> bool:
        """Reset password using reset token"""
        try:
            payload = self.verify_token(reset_token)
            if not payload or payload.get('type') != 'reset':
                return False
            
            user = User.query.get(payload['user_id'])
            if not user:
                return False
            
            # Hash new password
            new_hashed_password = self.hash_password(new_password)
            user.password_hash = new_hashed_password
            user.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Log audit event
            self.log_audit_event(user.id, 'password_reset', True)
            
            return True
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            db.session.rollback()
            return False


# Global auth manager instance
auth_manager = AuthManager()


def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        # Verify token
        user = auth_manager.get_user_from_token(token)
        if not user:
            return jsonify({'message': 'Invalid token'}), 401
        
        # Add user to request context
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


def require_admin(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user'):
            return jsonify({'message': 'Authentication required'}), 401
        
        # Check if user is admin (you can add admin field to User model)
        if not getattr(request.current_user, 'is_admin', False):
            return jsonify({'message': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def rate_limit(max_requests: int = 100, window: int = 3600):
    """Simple rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # In production, use Redis or similar for rate limiting
            # For now, we'll just pass through
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# OAuth flow helpers
def create_google_flow():
    """Create Google OAuth flow"""
    client_config = {
        "web": {
            "client_id": auth_manager.google_client_id,
            "client_secret": auth_manager.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:5000/api/auth/google/callback"]
        }
    }
    
    return Flow.from_client_config(
        client_config,
        scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
    )


def get_google_user_info(access_token: str) -> Optional[Dict[str, Any]]:
    """Get user info from Google using access token"""
    try:
        response = http_requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get Google user info: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error getting Google user info: {e}")
        return None 