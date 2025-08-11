"""
Production-grade authentication service with Redis caching
"""

import redis
import json
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        try:
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis unavailable, using memory fallback: {e}")
            self.redis_client = None
            self._memory_store = {}
        
        self.jwt_secret = secrets.token_urlsafe(32)
        self.token_expiry = 3600  # 1 hour
    
    def _hash_password(self, password: str, salt: str = None) -> tuple:
        if salt is None:
            salt = secrets.token_hex(32)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        return password_hash.hex(), salt
    
    def _verify_password(self, password: str, hash_hex: str, salt: str) -> bool:
        password_hash, _ = self._hash_password(password, salt)
        return password_hash == hash_hex
    
    def _set_cache(self, key: str, value: Dict, expiry: int = None):
        if self.redis_client:
            try:
                self.redis_client.setex(
                    key, 
                    expiry or self.token_expiry, 
                    json.dumps(value)
                )
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        else:
            self._memory_store[key] = value
    
    def _get_cache(self, key: str) -> Optional[Dict]:
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                return json.loads(data) if data else None
            except Exception as e:
                logger.error(f"Redis get error: {e}")
                return None
        else:
            return self._memory_store.get(key)
    
    def _del_cache(self, key: str):
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        else:
            self._memory_store.pop(key, None)
    
    def register_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        try:
            # Check if user exists
            user_key = f"user:{email}"
            if self._get_cache(user_key):
                return {"success": False, "error": "User already exists"}
            
            # Hash password
            password_hash, salt = self._hash_password(password)
            
            # Create user data
            user_id = secrets.token_urlsafe(16)
            user_data = {
                "id": user_id,
                "email": email,
                "name": name,
                "password_hash": password_hash,
                "salt": salt,
                "created_at": datetime.utcnow().isoformat(),
                "is_active": True
            }
            
            # Store user
            self._set_cache(user_key, user_data, expiry=None)
            self._set_cache(f"user_id:{user_id}", user_data, expiry=None)
            
            # Generate token
            token = self._generate_token(user_id, email)
            
            return {
                "success": True,
                "user": {
                    "id": user_id,
                    "email": email,
                    "name": name
                },
                "token": token
            }
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return {"success": False, "error": "Registration failed"}
    
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        try:
            # Get user data
            user_key = f"user:{email}"
            user_data = self._get_cache(user_key)
            
            if not user_data:
                return {"success": False, "error": "Invalid credentials"}
            
            # Verify password
            if not self._verify_password(password, user_data["password_hash"], user_data["salt"]):
                return {"success": False, "error": "Invalid credentials"}
            
            if not user_data.get("is_active", True):
                return {"success": False, "error": "Account deactivated"}
            
            # Generate token
            token = self._generate_token(user_data["id"], email)
            
            return {
                "success": True,
                "user": {
                    "id": user_data["id"],
                    "email": user_data["email"],
                    "name": user_data["name"]
                },
                "token": token
            }
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {"success": False, "error": "Login failed"}
    
    def _generate_token(self, user_id: str, email: str) -> str:
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": datetime.utcnow() + timedelta(seconds=self.token_expiry),
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        
        # Cache token
        token_key = f"token:{token}"
        self._set_cache(token_key, {"user_id": user_id, "email": email})
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            # Check cache first
            token_key = f"token:{token}"
            cached_data = self._get_cache(token_key)
            if not cached_data:
                return None
            
            # Verify JWT
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            
            return {
                "user_id": payload["user_id"],
                "email": payload["email"]
            }
            
        except jwt.ExpiredSignatureError:
            self._del_cache(f"token:{token}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    def logout_user(self, token: str) -> bool:
        try:
            self._del_cache(f"token:{token}")
            return True
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
