"""
Backend API for Wellness at Work
Flask-based REST API for data management and synchronization
"""

import os
import logging
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from models import db, User, BlinkEvent, SyncHistory
from storage import StorageManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Ensure instance directory exists first
instance_dir = Path(app.instance_path)
instance_dir.mkdir(exist_ok=True)

app.config.update({
    'SECRET_KEY': os.environ.get('SECRET_KEY', os.urandom(32).hex()),
    'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL', 'sqlite:///wellness.db'),
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY', os.urandom(32).hex()),
    'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=int(os.environ.get('JWT_EXPIRES_HOURS', '24'))),
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024  # 16MB max file size
})

# Initialize extensions
db.init_app(app)

# Log the database URI for debugging
logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

# CORS: allow CRA dev server by default; limit to GET/POST and Authorization header
_allowed = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000')
CORS(
    app,
    origins=[o.strip() for o in _allowed.split(',') if o.strip()],
    supports_credentials=False,
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)

# Initialize storage manager
storage_manager = StorageManager()


def token_required(f):
    """Decorator to require JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer TOKEN
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated


@app.route('/api/auth/register', methods=['POST'])
# Compatibility alias for clients using /signup
@app.route('/api/auth/signup', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Email and password are required'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'User already exists'}), 409
        
        # Create new user
        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            email=data['email'],
            name=data.get('name', ''),
            password_hash=hashed_password,
            consent=data.get('consent', False)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Generate token
        token = jwt.encode(
            {
                'user_id': new_user.id, 
                'email': new_user.email,
                'exp': datetime.now(timezone.utc) + app.config['JWT_ACCESS_TOKEN_EXPIRES']
            },
            app.config['JWT_SECRET_KEY'],
            algorithm="HS256"
        )
        
        return jsonify({
            'message': 'User created successfully',
            'token': token,
            'user': {
                'id': new_user.id,
                'email': new_user.email,
                'name': new_user.name
            }
        }), 201
        
    except Exception as e:
        logger.exception("Registration error")
        return jsonify({'message': 'Registration failed'}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Email and password are required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user:
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Check if this is an OAuth user (no password hash)
        if user.password_hash is None:
            return jsonify({'message': 'Please use Google login for this account'}), 401
        
        if not check_password_hash(user.password_hash, data['password']):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Generate token
        token = jwt.encode(
            {
                'user_id': user.id, 
                'email': user.email,
                'exp': datetime.now(timezone.utc) + app.config['JWT_ACCESS_TOKEN_EXPIRES']
            },
            app.config['JWT_SECRET_KEY'],
            algorithm="HS256"
        )
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name
            }
        }), 200
        
    except Exception as e:
        logger.exception("Login error")
        return jsonify({'message': 'Login failed'}), 500


@app.route('/api/auth/google', methods=['POST'])
def google_auth():
    """Google OAuth authentication"""
    try:
        data = request.get_json()
        logger.info(f"Google auth data: {data}")
        
        if not data or not data.get('email'):
            logger.error("Email is missing from Google auth request")
            return jsonify({'message': 'Email is required'}), 400
        
        # Check if user exists
        user = User.query.filter_by(email=data['email']).first()
        logger.info(f"Existing user found: {user is not None}")
        
        if not user:
            # Create new user for Google OAuth (no password hash needed)
            logger.info("Creating new Google OAuth user")
            user = User(
                email=data['email'],
                name=data.get('name', ''),
                password_hash=None,  # OAuth users don't have password
                consent=True
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f"New user created with ID: {user.id}")
        
        # Generate token
        token = jwt.encode(
            {
                'user_id': user.id, 
                'email': user.email,
                'exp': datetime.now(timezone.utc) + app.config['JWT_ACCESS_TOKEN_EXPIRES']
            },
            app.config['JWT_SECRET_KEY'],
            algorithm="HS256"
        )
        
        logger.info(f"Token generated for user: {user.id}")
        
        return jsonify({
            'message': 'Authentication successful',
            'token': token,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name
            }
        }), 200
        
    except Exception:
        logger.exception("Google auth error")
        return jsonify({'message': 'Authentication failed'}), 500


@app.route('/api/auth/google', methods=['GET'])
def google_oauth_start():
    """Initiate Google OAuth by redirecting to Google's consent screen (dev convenience)."""
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    redirect_origin = request.headers.get('Origin') or request.args.get('origin') or 'http://localhost:3000'
    redirect_uri = redirect_origin.rstrip('/') + '/auth/callback'
    if not client_id:
        return jsonify({'status': 'offline', 'message': 'OAuth not configured', 'redirect_uri': redirect_uri}), 200
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile openid',
        'access_type': 'offline',
        'include_granted_scopes': 'true',
        'prompt': 'consent'
    }
    from urllib.parse import urlencode
    auth_url = 'https://accounts.google.com/o/oauth2/auth?' + urlencode(params)
    from flask import redirect
    return redirect(auth_url, code=302)


@app.route('/api/auth/google/callback', methods=['POST'])
def google_callback():
    """Handle Google OAuth callback"""
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code:
            return jsonify({'message': 'Authorization code required'}), 400
            
        # Exchange code for token and user info
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import Flow

        # Read OAuth client from environment to avoid hardcoding secrets
        client_id = os.environ.get('GOOGLE_CLIENT_ID')
        client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')

        # If missing, respond safely without crashing (offline/dev mode)
        if not client_id or not client_secret:
            logger.warning("Google OAuth client credentials not configured; returning offline response")
            # In dev/offline mode, allow front-end to proceed with a fake minimal profile
            return jsonify({'message': 'OAuth not configured', 'status': 'offline'}), 200

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=['https://www.googleapis.com/auth/userinfo.email',
                   'https://www.googleapis.com/auth/userinfo.profile', 'openid']
        )
        flow.redirect_uri = request.headers.get('Origin', 'http://localhost:3000') + '/auth/callback'
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get user info
        import requests as req
        response = req.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {credentials.token}'}
        )
        user_info = response.json()
        
        return jsonify({
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'id': user_info.get('id')
        }), 200
        
    except Exception as e:
        logger.error(f"Google callback error: {e}")
        return jsonify({'message': 'Callback failed'}), 500


@app.route('/api/auth/validate', methods=['POST'])
@token_required
def validate_token(current_user):
    """Validate JWT token and return user info"""
    try:
        return jsonify({
            'message': 'Token valid',
            'user': {
                'id': current_user.id,
                'email': current_user.email,
                'name': current_user.name
            }
        }), 200
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return jsonify({'message': 'Token validation failed'}), 500


@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout(current_user):
    """Logout user (optional endpoint for cleanup)"""
    try:
        # In a more complex system, you might invalidate the token here
        # For now, just log the logout
        logger.info(f"User logged out: {current_user.email}")
        return jsonify({'message': 'Logout successful'}), 200
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'message': 'Logout failed'}), 500


@app.route('/api/blink-data', methods=['POST'])
@token_required
def submit_blink_data(current_user):
    """Submit blink tracking data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        # Parse timestamp
        timestamp = data.get('timestamp')
        if timestamp:
            if isinstance(timestamp, str):
                # Convert ISO string to timestamp
                from datetime import datetime as dt
                timestamp = dt.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp()
        else:
            timestamp = datetime.now(timezone.utc).timestamp()
        
        # Create blink event
        blink_event = BlinkEvent(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            timestamp=timestamp,
            count=data.get('blink_count', 0),
            session_id=data.get('session_id', ''),
            device_id=data.get('device_id', '')
        )
        
        db.session.add(blink_event)
        db.session.commit()
        
        # Store in local JSON format
        json_data = {
            str(blink_event.id): {
                "open_closed": data.get('open_closed', 'Open'),
                "direction": data.get('direction', 'Straight'),
                "timestamp": blink_event.timestamp,
                "blink_count": blink_event.count,
                "session_id": blink_event.session_id,
                "device_id": blink_event.device_id
            }
        }
        
        # Try cloud storage first, fallback to local JSON
        try:
            storage_manager.store_event(blink_event)
        except Exception as storage_error:
            logger.warning(f"Cloud storage failed, saving to local JSON: {storage_error}")
            # Save to local JSON file
            json_file = f"data/blink_data_{current_user.id}.json"
            os.makedirs(os.path.dirname(json_file), exist_ok=True)
            
            # Load existing data or create new
            try:
                with open(json_file, 'r') as f:
                    existing_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = {}
            
            # Merge with new data
            existing_data.update(json_data)
            
            # Save updated data
            with open(json_file, 'w') as f:
                json.dump(existing_data, f, indent=2)
        
        return jsonify({
            'message': 'Blink data submitted',
            'event_id': blink_event.id
        }), 201
        
    except Exception as e:
        logger.error(f"Error submitting blink data: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to submit blink data'}), 500


@app.route('/api/blink-events', methods=['GET'])
@token_required
def get_blink_events(current_user):
    """Get blink events for the current user"""
    try:
        # Query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 100))
        
        # Build query
        query = BlinkEvent.query.filter_by(user_id=current_user.id)
        
        if start_date:
            start_datetime = datetime.fromisoformat(start_date)
            query = query.filter(BlinkEvent.timestamp >= start_datetime.timestamp())
        
        if end_date:
            end_datetime = datetime.fromisoformat(end_date)
            query = query.filter(BlinkEvent.timestamp <= end_datetime.timestamp())
        
        # Execute query
        events = query.order_by(BlinkEvent.timestamp.desc()).limit(limit).all()
        
        # Convert to JSON
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'timestamp': event.timestamp,
                'count': event.count,
                'session_id': event.session_id,
                'device_id': event.device_id,
                'created_at': event.created_at.isoformat()
            })
        
        return jsonify({
            'events': events_data,
            'total': len(events_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching blink events: {e}")
        return jsonify({'error': 'Failed to fetch blink events'}), 500


@app.route('/api/user/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """Get user profile"""
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'name': current_user.name,
        'consent': current_user.consent,
        'created_at': current_user.created_at.isoformat()
    }), 200


@app.route('/api/sync/status', methods=['GET'])
@token_required
def sync_status(current_user):
    """Get sync status"""
    try:
        last_sync = SyncHistory.query.filter_by(user_id=current_user.id).order_by(SyncHistory.timestamp.desc()).first()
        
        return jsonify({
            'last_sync': last_sync.timestamp.isoformat() if last_sync else None,
            'status': last_sync.status if last_sync else 'never_synced',
            'message': last_sync.message if last_sync else 'No sync history'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        return jsonify({'error': 'Failed to get sync status'}), 500


@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'Wellness at Work API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'auth': {
                'register': '/api/auth/register',
                'login': '/api/auth/login',
                'google': '/api/auth/google'
            },
            'data': {
                'blink_data': '/api/blink-data',
                'blink_events': '/api/blink-events'
            },
            'user': {
                'profile': '/api/user/profile'
            }
        }
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Wellness at Work API is running',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error'}), 500


if __name__ == '__main__':
    with app.app_context():
        # Ensure instance directory exists
        os.makedirs(app.instance_path, exist_ok=True)
        db.create_all()
        logger.info("Database tables created successfully")
    
    logger.info("Starting Flask server on 0.0.0.0:5000...")
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except OSError as e:
        logger.error(f"Failed to bind to port 5000: {e}")
        logger.info("Trying port 5001...")
        app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
