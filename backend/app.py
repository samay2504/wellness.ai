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

"""IMPORTANT: Always import models via package-relative path to ensure a single
module instance (prevents duplicate SQLAlchemy() objects causing 'app not registered'
runtime errors in tests). We still keep an absolute fallback for direct script runs.
"""
try:
    from .models import db, User, BlinkEvent, SyncHistory  # type: ignore
except ImportError:  # When executed as script without package context
    from models import db, User, BlinkEvent, SyncHistory  # type: ignore
try:
    from .storage import StorageManager  # type: ignore
except ImportError:  # script execution fallback
    from storage import StorageManager  # type: ignore
from werkzeug.exceptions import BadRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
    
# Lightweight health check (unauthenticated) for tooling & UI readiness probes
@app.route('/api/health', methods=['GET'])
def api_health():  # distinct name to avoid clashing with existing /health route
    return jsonify({"status": "ok"}), 200

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
        # Use silent JSON parsing to avoid raising BadRequest which was causing 500s
        raw = request.get_data(cache=False, as_text=True) or ''
        data = request.get_json(silent=True)
        if data is None:
            # Attempt manual parse for clearer diagnostics
            try:
                data = json.loads(raw)
            except Exception:
                logger.warning("Registration attempt with invalid JSON body: %s", raw[:200])
                return jsonify({'message': 'Invalid JSON body'}), 400
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
        logger.exception(f"Registration error: {e}")
        return jsonify({'message': f'Registration failed: {str(e)}'}), 500


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
def submit_blink_data():
    """Submit blink tracking data.

    Accepts authenticated or (if ALLOW_ANONYMOUS_INGEST=1/true) anonymous events with device+session ids.
    """
    allow_anon = os.environ.get('ALLOW_ANONYMOUS_INGEST', 'true').lower() in ('1','true','yes')
    auth_user = None
    # Attempt auth if header present
    if 'Authorization' in request.headers:
        try:
            token = request.headers['Authorization'].split()[1]
            data_tok = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            auth_user = User.query.get(data_tok['user_id'])
        except Exception as e:
            if not allow_anon:
                return jsonify({'message':'Invalid token','status':'error'}), 401
    if not auth_user and not allow_anon:
        return jsonify({'message':'Authentication required','status':'error'}), 401
    try:
        data = request.get_json() or {}
        if not data:
            return jsonify({'message':'No data provided'}), 400
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            from datetime import datetime as dt
            timestamp = dt.fromisoformat(timestamp.replace('Z','+00:00')).timestamp()
        if not timestamp:
            timestamp = datetime.now(timezone.utc).timestamp()
        device_id = data.get('device_id') or data.get('deviceId') or 'unknown-device'
        session_id = data.get('session_id') or data.get('sessionId') or str(uuid.uuid4())
        if auth_user:
            user_id = auth_user.id
        else:
            # Create or get a dedicated anonymous user so FK constraint is satisfied
            anon_email = 'anonymous@localhost'
            anon = User.query.filter_by(email=anon_email).first()
            if not anon:
                anon = User(email=anon_email, name='Anonymous', password_hash=None, consent=False)
                db.session.add(anon)
                db.session.commit()
            user_id = anon.id
        blink_event = BlinkEvent(
            id=str(uuid.uuid4()),
            user_id=user_id if user_id is not None else 0,
            timestamp=timestamp,
            count=data.get('blink_count', data.get('count', 0)),
            session_id=session_id,
            device_id=device_id,
            duration_ms=data.get('duration_ms'),
            eye_aspect_ratio=data.get('eye_aspect_ratio'),
            gaze_x=data.get('gaze_x'),
            gaze_y=data.get('gaze_y'),
            os=data.get('os'),
            app_version=data.get('app_version')
        )
        try:
            db.session.add(blink_event)
            db.session.commit()
        except Exception as e:
            logger.error(f"DB insert failed for blink event: {e}")
            db.session.rollback()
        try:
            storage_manager.store_event(blink_event)
        except Exception as e:
            logger.warning(f"Storage manager store_event error: {e}")
        # Record lightweight sync history so dashboard status updates
        try:
            sync_row = SyncHistory(
                user_id=user_id if user_id is not None else 0,
                timestamp=timestamp,
                events_synced=1,
                success=True,
                error_message=None
            )
            db.session.add(sync_row)
            db.session.commit()
        except Exception as e:
            logger.debug(f"SyncHistory insert failed: {e}")
            db.session.rollback()
        return jsonify({'message':'Blink data submitted','event_id':blink_event.id,'anonymous': auth_user is None}), 201
    except Exception as e:
        logger.error(f"Error submitting blink data: {e}")
        return jsonify({'error':'Failed to submit blink data'}), 500

# ------------------- New stub analytics/performance endpoints -------------------
@app.route('/api/performance/metrics', methods=['GET'])
def performance_metrics_stub():
    """Return simple system metrics for dashboard charts.

    Uses psutil if available; otherwise returns zeros with Low energy impact.
    """
    try:
        cpu_percent = 0.0
        memory_percent = 0.0
        energy_impact = 'Low'
        try:
            import psutil  # type: ignore
            cpu_percent = psutil.cpu_percent(interval=0.0)
            memory_percent = psutil.virtual_memory().percent
            if cpu_percent > 70 or memory_percent > 80:
                energy_impact = 'High'
            elif cpu_percent > 35 or memory_percent > 50:
                energy_impact = 'Medium'
        except Exception:
            pass
        return jsonify({'cpu_percent': cpu_percent, 'memory_percent': memory_percent, 'energy_impact': energy_impact, 'status': 'ok'}), 200
    except Exception as e:
        logger.warning(f"performance metrics error: {e}")
        return jsonify({'cpu_percent':0,'memory_percent':0,'energy_impact':'Low','status':'degraded'}), 200

@app.route('/api/analytics', methods=['GET'])
def analytics_stub():
    return jsonify({'range': request.args.get('range','30d'), 'data':{}, 'status':'ok'}), 200

@app.route('/api/analytics/insights', methods=['GET'])
def analytics_insights_stub():
    return jsonify({'insights':[], 'status':'ok'}), 200

@app.route('/api/sync/flush', methods=['POST'])
def sync_flush():
    summary = storage_manager.sync_flush() if hasattr(storage_manager,'sync_flush') else {'status':'unsupported'}
    code = 200 if summary.get('status') == 'ok' else (403 if summary.get('status') == 'blocked' else 500)
    return jsonify({'message':'flush attempted', 'summary': summary}), code


@app.route('/api/analytics/blinks', methods=['GET'])
@token_required
def blink_analytics(current_user):
    """Return blink time series analytics (PNG base64 + plotly JSON)."""
    try:
        # Date range handling
        start = request.args.get('start')
        end = request.args.get('end')
        query = BlinkEvent.query.filter_by(user_id=current_user.id)
        if start:
            start_dt = datetime.fromisoformat(start)
            query = query.filter(BlinkEvent.timestamp >= start_dt.timestamp())
        if end:
            end_dt = datetime.fromisoformat(end)
            query = query.filter(BlinkEvent.timestamp <= end_dt.timestamp())
        events = query.order_by(BlinkEvent.timestamp).all()
        if not events:
            return jsonify({'events': [], 'png_base64': None, 'plotly': None}), 200
        import base64, io
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        timestamps = [datetime.fromtimestamp(e.timestamp, tz=timezone.utc) for e in events]
        counts = [e.count for e in events]
        fig, ax = plt.subplots(figsize=(6,3))
        ax.plot(timestamps, counts, marker='o', linewidth=1)
        ax.set_title('Blink Counts')
        ax.set_xlabel('Time')
        ax.set_ylabel('Count')
        fig.autofmt_xdate()
        buf = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)
        png_b64 = base64.b64encode(buf.read()).decode('utf-8')
        # Plotly JSON
        try:
            import plotly.graph_objects as go
            ply_fig = go.Figure(data=[go.Scatter(x=timestamps, y=counts, mode='lines+markers', name='Blinks')])
            ply_fig.update_layout(title='Blink Counts', xaxis_title='Time', yaxis_title='Count')
            plotly_json = ply_fig.to_dict()
        except Exception as e:
            logger.warning(f"Plotly generation failed: {e}")
            plotly_json = None
        return jsonify({
            'events': [e.to_dict() for e in events],
            'png_base64': png_b64,
            'plotly': plotly_json
        }), 200
    except Exception as e:
        logger.error(f"Analytics generation failed: {e}")
        return jsonify({'error': 'Failed to generate analytics'}), 500


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
        
        # Aggregate metrics expected by dashboard
        total_blinks = sum(e['count'] for e in events_data)
        if events_data:
            ts_vals = [e['timestamp'] for e in events_data]
            span_seconds = max(ts_vals) - min(ts_vals)
            span_minutes = max(span_seconds / 60.0, 1)
        else:
            span_minutes = 1
        avg_blink_rate = round(total_blinks / span_minutes, 2) if total_blinks else 0
        active_hours = round(span_minutes / 60.0, 2) if total_blinks else 0
        health_score = 85 if total_blinks else 0
        return jsonify({
            'events': events_data,
            'total': len(events_data),
            'total_blinks': total_blinks,
            'avg_blink_rate': avg_blink_rate,
            'active_hours': active_hours,
            'health_score': health_score
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching blink events: {e}")
        return jsonify({'error': 'Failed to fetch blink events'}), 500


@app.route('/api/user/profile', methods=['GET'])
@token_required
def user_profile(current_user):
    """Return current user profile (added for frontend AuthContext)."""
    try:
        return jsonify({
            'id': current_user.id,
            'email': current_user.email,
            'name': current_user.name
        }), 200
    except Exception as e:
        logger.error(f"Profile error: {e}")
        return jsonify({'message': 'Profile fetch failed'}), 500


@app.route('/api/sync/status', methods=['GET'])
@token_required
def sync_status(current_user):
    """Compute sync status for dashboard.

    Status rules:
      connected: last successful sync <5min ago
      stale: last successful sync >=5min ago
      error: last sync failed
      never_synced: no history
    Also returns pending_events from local queue if present.
    """
    try:
        last_sync = SyncHistory.query.filter_by(user_id=current_user.id).order_by(SyncHistory.timestamp.desc()).first()
        if last_sync:
            last_dt = datetime.fromtimestamp(last_sync.timestamp, tz=timezone.utc)
            age = (datetime.now(timezone.utc) - last_dt).total_seconds()
            if last_sync.success:
                status = 'connected' if age < 300 else 'stale'
                message = 'Last successful sync'
            else:
                status = 'error'
                message = last_sync.error_message or 'Last sync failed'
            last_iso = last_dt.isoformat()
        else:
            status = 'never_synced'
            message = 'No sync history'
            last_iso = None
        pending_events = 0
        try:
            qf = getattr(storage_manager, 'queue_file', None)
            if qf and os.path.exists(qf):
                with open(qf, 'r', encoding='utf-8') as f:
                    pending_events = sum(1 for line in f if line.strip())
        except Exception:
            pass
        return jsonify({'last_sync': last_iso, 'status': status, 'message': message, 'pending_events': pending_events}), 200
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
            'health': '/health',  # detailed health
            'api_health': '/api/health',  # lightweight probe
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
