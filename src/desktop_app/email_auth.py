"""
Enhanced email authentication with GDPR-compliant secure storage
Provides direct email/password authentication with production security
"""

import os
import json
import logging
import hashlib
import requests
import keyring
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv('API_BASE_URL', 'http://127.0.0.1:5000')

@dataclass
class EmailUser:
    """Email-based user data model"""
    id: str
    name: str
    email: str
    token: str
    consent_preferences: Dict[str, bool] = None
    consent: bool = True

class EmailAuthManager:
    """GDPR-compliant email-based authentication manager"""
    
    def __init__(self):
        self.current_user: Optional[EmailUser] = None
        self.use_local_storage = True  # Use local secure storage by default
        
        # Initialize secure storage
        try:
            from desktop_app.secure_storage import secure_data_manager
            self.secure_storage = secure_data_manager
        except ImportError:
            logger.warning("Secure storage not available, using keyring fallback")
            self.secure_storage = None
            
    def _hash_password(self, password: str, salt: str = None) -> tuple[str, str]:
        """Hash password securely"""
        if salt is None:
            salt = os.urandom(32).hex()
        
        # Use PBKDF2 with SHA-256
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                           password.encode('utf-8'), 
                                           salt.encode('utf-8'), 
                                           100000)  # 100,000 iterations
        return password_hash.hex(), salt
        
    def register(self, email: str, password: str, name: str, 
                consent_preferences: Dict[str, bool] = None) -> Optional[EmailUser]:
        """Register a new user with email and password"""
        try:
            # Hash password securely
            password_hash, salt = self._hash_password(password)
            full_hash = f"{salt}:{password_hash}"
            
            if consent_preferences is None:
                consent_preferences = {
                    'essential': True,
                    'analytics': False,
                    'marketing': False
                }
            
            if self.secure_storage and self.use_local_storage:
                # Use local secure storage
                try:
                    user_id = self.secure_storage.register_user(
                        email=email,
                        name=name,
                        password_hash=full_hash,
                        consent_preferences=consent_preferences
                    )
                    
                    # Generate local token
                    token = self._generate_local_token(user_id, email)
                    
                    user = EmailUser(
                        id=user_id,
                        name=name,
                        email=email,
                        token=token,
                        consent_preferences=consent_preferences,
                        consent=True
                    )
                    
                    # Store credentials securely
                    self._save_credentials(user)
                    self.current_user = user
                    logger.info(f"User registered locally: {email}")
                    return user
                    
                except ValueError as e:
                    logger.error(f"Local registration failed: {e}")
                    return None
            
            else:
                # Fallback to backend registration
                response = requests.post(f'{API_BASE_URL}/api/auth/register', json={
                    'email': email,
                    'password': password,
                    'name': name,
                    'consent_preferences': consent_preferences
                }, timeout=10)
                
                if response.status_code == 201:
                    data = response.json()
                    user = EmailUser(
                        id=str(data['user']['id']),
                        name=data['user']['name'],
                        email=data['user']['email'],
                        token=data['token'],
                        consent_preferences=consent_preferences,
                        consent=True
                    )
                    
                    # Store credentials securely
                    self._save_credentials(user)
                    self.current_user = user
                    logger.info(f"User registered via backend: {email}")
                    return user
                else:
                    error_msg = response.json().get('message', 'Registration failed')
                    logger.error(f"Backend registration failed: {error_msg}")
                    return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Registration request failed: {e}")
            # Try local storage as fallback
            if self.secure_storage and not self.use_local_storage:
                logger.info("Falling back to local storage")
                self.use_local_storage = True
                return self.register(email, password, name, consent_preferences)
            return None
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return None
    
    def login(self, email: str, password: str) -> Optional[EmailUser]:
        """Login with email and password"""
        try:
            if self.secure_storage and self.use_local_storage:
                # Use local secure storage
                password_hash, _ = self._hash_password(password)
                user_data = self.secure_storage.authenticate_user(email, password_hash)
                
                if user_data:
                    token = self._generate_local_token(user_data['id'], email)
                    
                    user = EmailUser(
                        id=user_data['id'],
                        name=user_data['name'],
                        email=user_data['email'],
                        token=token,
                        consent_preferences=user_data.get('consent_preferences', {}),
                        consent=True
                    )
                    
                    # Store credentials securely
                    self._save_credentials(user)
                    self.current_user = user
                    logger.info(f"User logged in locally: {email}")
                    return user
                else:
                    logger.error("Local login failed: Invalid credentials")
                    return None
            
            else:
                # Backend authentication
                response = requests.post(f'{API_BASE_URL}/api/auth/login', json={
                    'email': email,
                    'password': password
                }, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    user = EmailUser(
                        id=str(data['user']['id']),
                        name=data['user']['name'],
                        email=data['user']['email'],
                        token=data['token'],
                        consent_preferences=data.get('consent_preferences', {}),
                        consent=True
                    )
                    
                    # Store credentials securely
                    self._save_credentials(user)
                    self.current_user = user
                    logger.info(f"User logged in via backend: {email}")
                    return user
                else:
                    error_msg = response.json().get('message', 'Login failed')
                    logger.error(f"Backend login failed: {error_msg}")
                    return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Login request failed: {e}")
            # Try local storage as fallback
            if self.secure_storage and not self.use_local_storage:
                logger.info("Falling back to local storage")
                self.use_local_storage = True
                return self.login(email, password)
            return None
        except Exception as e:
            logger.error(f"Login error: {e}")
            return None
    
    def _generate_local_token(self, user_id: str, email: str) -> str:
        """Generate local authentication token"""
        import time
        import base64
        
        token_data = {
            'user_id': user_id,
            'email': email,
            'issued_at': int(time.time()),
            'expires_at': int(time.time()) + (30 * 24 * 60 * 60)  # 30 days
        }
        
        token_str = json.dumps(token_data)
        return base64.b64encode(token_str.encode()).decode()
    
    def auto_login(self) -> Optional[EmailUser]:
        """Attempt to login with stored credentials"""
        try:
            stored_creds = self._load_credentials()
            if stored_creds:
                if self.use_local_storage:
                    # Validate local token
                    if self._validate_local_token(stored_creds['token']):
                        user = EmailUser(
                            id=stored_creds['id'],
                            name=stored_creds['name'],
                            email=stored_creds['email'],
                            token=stored_creds['token'],
                            consent_preferences=stored_creds.get('consent_preferences', {}),
                            consent=stored_creds.get('consent', True)
                        )
                        self.current_user = user
                        logger.info(f"Auto-login successful (local): {user.email}")
                        return user
                
                else:
                    # Validate token with backend
                    response = requests.post(f'{API_BASE_URL}/api/auth/validate', 
                                           headers={'Authorization': f'Bearer {stored_creds["token"]}'}, 
                                           timeout=10)
                    
                    if response.status_code == 200:
                        user = EmailUser(
                            id=stored_creds['id'],
                            name=stored_creds['name'],
                            email=stored_creds['email'],
                            token=stored_creds['token'],
                            consent_preferences=stored_creds.get('consent_preferences', {}),
                            consent=stored_creds.get('consent', True)
                        )
                        self.current_user = user
                        logger.info(f"Auto-login successful (backend): {user.email}")
                        return user
                    else:
                        logger.info("Stored token is invalid, clearing credentials")
                        self._clear_credentials()
                        
        except requests.exceptions.RequestException as e:
            logger.error(f"Auto-login request failed: {e}")
            # Try local validation as fallback
            if not self.use_local_storage:
                self.use_local_storage = True
                return self.auto_login()
        except Exception as e:
            logger.error(f"Auto-login error: {e}")
            
        return None
    
    def _validate_local_token(self, token: str) -> bool:
        """Validate local token"""
        try:
            import base64
            import time
            
            token_str = base64.b64decode(token.encode()).decode()
            token_data = json.loads(token_str)
            
            # Check if token is expired
            if token_data.get('expires_at', 0) < time.time():
                logger.info("Local token expired")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False
    
    def logout(self):
        """Logout current user"""
        try:
            if self.current_user:
                if not self.use_local_storage:
                    # Notify backend
                    requests.post(f'{API_BASE_URL}/api/auth/logout',
                                headers={'Authorization': f'Bearer {self.current_user.token}'},
                                timeout=5)
                
            self._clear_credentials()
            self.current_user = None
            logger.info("User logged out successfully")
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.current_user is not None
    
    def get_current_user(self) -> Optional[EmailUser]:
        """Get current authenticated user"""
        return self.current_user
    
    def _save_credentials(self, user: EmailUser):
        """Save user credentials to secure storage"""
        try:
            creds = {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'token': user.token,
                'consent_preferences': user.consent_preferences,
                'consent': user.consent
            }
            keyring.set_password("wellness_ai", "email_auth", json.dumps(creds))
            logger.info("Credentials saved to secure storage")
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
    
    def _load_credentials(self) -> Optional[Dict[str, Any]]:
        """Load user credentials from secure storage"""
        try:
            creds_json = keyring.get_password("wellness_ai", "email_auth")
            if creds_json:
                return json.loads(creds_json)
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
        return None
    
    def _clear_credentials(self):
        """Clear stored credentials"""
        try:
            keyring.delete_password("wellness_ai", "email_auth")
            logger.info("Credentials cleared from secure storage")
        except Exception as e:
            logger.warning(f"Failed to clear credentials: {e}")
    
    def request_data_export(self) -> Optional[Dict[str, Any]]:
        """Request user data export (GDPR Article 20)"""
        if not self.current_user:
            return None
            
        try:
            if self.secure_storage and self.use_local_storage:
                return self.secure_storage.get_user_data_export(self.current_user.id)
            else:
                # Request from backend
                response = requests.get(f'{API_BASE_URL}/api/user/data-export',
                                      headers={'Authorization': f'Bearer {self.current_user.token}'},
                                      timeout=30)
                if response.status_code == 200:
                    return response.json()
            
        except Exception as e:
            logger.error(f"Data export failed: {e}")
        
        return None
    
    def request_data_deletion(self, hard_delete: bool = False) -> bool:
        """Request user data deletion (GDPR Article 17)"""
        if not self.current_user:
            return False
            
        try:
            if self.secure_storage and self.use_local_storage:
                self.secure_storage.delete_user_data(self.current_user.id, hard_delete)
                self.logout()
                return True
            else:
                # Request from backend
                response = requests.delete(f'{API_BASE_URL}/api/user/data',
                                         headers={'Authorization': f'Bearer {self.current_user.token}'},
                                         json={'hard_delete': hard_delete},
                                         timeout=30)
                if response.status_code == 200:
                    self.logout()
                    return True
            
        except Exception as e:
            logger.error(f"Data deletion failed: {e}")
        
        return False

# Global instance for backward compatibility
email_auth_manager = EmailAuthManager()
