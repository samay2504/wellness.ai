"""
Database models for Wellness at Work
SQLAlchemy models for user data and blink events
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utc_now():
    """Helper function to get current UTC time for SQLAlchemy defaults"""
    return datetime.now(timezone.utc)


class User(db.Model):
    """User model for authentication and profile data"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Allow null for OAuth users
    consent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationships
    blink_events = db.relationship('BlinkEvent', backref='user', lazy=True, cascade='all, delete-orphan')
    sync_history = db.relationship('SyncHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    device_info = db.relationship('DeviceInfo', backref='user', lazy=True, cascade='all, delete-orphan')
    session_info = db.relationship('SessionInfo', backref='user', lazy=True, cascade='all, delete-orphan')
    privacy_settings = db.relationship('PrivacySettings', backref='user', lazy=True, uselist=False, cascade='all, delete-orphan')
    user_settings = db.relationship('UserSettings', backref='user', lazy=True, uselist=False, cascade='all, delete-orphan')
    wellness_goals = db.relationship('WellnessGoals', backref='user', lazy=True, uselist=False, cascade='all, delete-orphan')
    performance_metrics = db.relationship('PerformanceMetrics', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    analytics_data = db.relationship('AnalyticsData', backref='user', lazy=True, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'consent': self.consent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class BlinkEvent(db.Model):
    """Blink event model for tracking eye blinks"""
    __tablename__ = 'blink_events'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.Float, nullable=False)  # Unix timestamp
    count = db.Column(db.Integer, nullable=False, default=0)
    session_id = db.Column(db.String(36), nullable=False)  # Session UUID
    device_id = db.Column(db.String(50), nullable=False)
    synced = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    def __repr__(self):
        return f'<BlinkEvent {self.id} - User {self.user_id}>'
    
    def to_dict(self):
        """Convert blink event to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'timestamp': self.timestamp,
            'count': self.count,
            'session_id': self.session_id,
            'device_id': self.device_id,
            'synced': self.synced,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SyncHistory(db.Model):
    """Sync history model for tracking synchronization events"""
    __tablename__ = 'sync_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.Float, nullable=False)  # Unix timestamp
    events_synced = db.Column(db.Integer, nullable=False, default=0)
    success = db.Column(db.Boolean, nullable=False, default=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    def __repr__(self):
        return f'<SyncHistory {self.id} - User {self.user_id}>'
    
    def to_dict(self):
        """Convert sync history to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'timestamp': self.timestamp,
            'events_synced': self.events_synced,
            'success': self.success,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DeviceInfo(db.Model):
    """Device information model for tracking user devices"""
    __tablename__ = 'device_info'
    
    id = db.Column(db.String(50), primary_key=True)  # Device ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    device_name = db.Column(db.String(100), nullable=True)
    platform = db.Column(db.String(50), nullable=True)  # Windows, macOS, Linux
    version = db.Column(db.String(20), nullable=True)  # App version
    last_seen = db.Column(db.DateTime, default=utc_now)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    def __repr__(self):
        return f'<DeviceInfo {self.id} - User {self.user_id}>'
    
    def to_dict(self):
        """Convert device info to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'device_name': self.device_name,
            'platform': self.platform,
            'version': self.version,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SessionInfo(db.Model):
    """Session information model for tracking user sessions"""
    __tablename__ = 'session_info'
    
    id = db.Column(db.String(36), primary_key=True)  # Session UUID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    device_id = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.Float, nullable=False)  # Unix timestamp
    end_time = db.Column(db.Float, nullable=True)  # Unix timestamp
    total_blinks = db.Column(db.Integer, default=0)
    duration_minutes = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    def __repr__(self):
        return f'<SessionInfo {self.id} - User {self.user_id}>'
    
    def to_dict(self):
        """Convert session info to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'device_id': self.device_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'total_blinks': self.total_blinks,
            'duration_minutes': self.duration_minutes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PrivacySettings(db.Model):
    """Privacy settings model for GDPR compliance"""
    __tablename__ = 'privacy_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    data_retention_days = db.Column(db.Integer, default=730)  # 2 years default
    allow_analytics = db.Column(db.Boolean, default=False)
    allow_marketing = db.Column(db.Boolean, default=False)
    allow_third_party = db.Column(db.Boolean, default=False)
    auto_delete_inactive = db.Column(db.Boolean, default=True)
    anonymize_after_days = db.Column(db.Integer, default=365)  # 1 year default
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    def __repr__(self):
        return f'<PrivacySettings User {self.user_id}>'
    
    def to_dict(self):
        """Convert privacy settings to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'data_retention_days': self.data_retention_days,
            'allow_analytics': self.allow_analytics,
            'allow_marketing': self.allow_marketing,
            'allow_third_party': self.allow_third_party,
            'auto_delete_inactive': self.auto_delete_inactive,
            'anonymize_after_days': self.anonymize_after_days,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AuditLog(db.Model):
    """Audit log model for security and compliance tracking"""
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)  # login, logout, data_export, etc.
    resource = db.Column(db.String(100), nullable=True)  # endpoint or resource accessed
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    user_agent = db.Column(db.Text, nullable=True)
    success = db.Column(db.Boolean, default=True)
    details = db.Column(db.Text, nullable=True)  # JSON details
    timestamp = db.Column(db.DateTime, default=utc_now)
    
    def __repr__(self):
        return f'<AuditLog {self.id} - {self.action}>'
    
    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource': self.resource,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'success': self.success,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class UserSettings(db.Model):
    """User settings model for application preferences"""
    __tablename__ = 'user_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    theme = db.Column(db.String(20), default='light')  # light, dark, auto
    language = db.Column(db.String(10), default='en')
    timezone = db.Column(db.String(50), default='UTC')
    notifications_enabled = db.Column(db.Boolean, default=True)
    email_notifications = db.Column(db.Boolean, default=True)
    push_notifications = db.Column(db.Boolean, default=True)
    desktop_notifications = db.Column(db.Boolean, default=True)
    blink_reminders = db.Column(db.Boolean, default=True)
    break_reminders = db.Column(db.Boolean, default=True)
    weekly_reports = db.Column(db.Boolean, default=True)
    data_sharing = db.Column(db.Boolean, default=False)
    analytics_tracking = db.Column(db.Boolean, default=False)
    third_party_access = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    def __repr__(self):
        return f'<UserSettings User {self.user_id}>'
    
    def to_dict(self):
        """Convert user settings to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'theme': self.theme,
            'language': self.language,
            'timezone': self.timezone,
            'notifications_enabled': self.notifications_enabled,
            'email_notifications': self.email_notifications,
            'push_notifications': self.push_notifications,
            'desktop_notifications': self.desktop_notifications,
            'blink_reminders': self.blink_reminders,
            'break_reminders': self.break_reminders,
            'weekly_reports': self.weekly_reports,
            'data_sharing': self.data_sharing,
            'analytics_tracking': self.analytics_tracking,
            'third_party_access': self.third_party_access,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class WellnessGoals(db.Model):
    """Wellness goals model for user-defined targets"""
    __tablename__ = 'wellness_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    daily_blinks = db.Column(db.Integer, default=1200)
    screen_breaks = db.Column(db.Integer, default=8)
    max_screen_time = db.Column(db.Float, default=8.0)  # hours
    blink_rate_target = db.Column(db.Float, default=15.0)  # blinks per minute
    break_duration = db.Column(db.Integer, default=20)  # minutes
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    def __repr__(self):
        return f'<WellnessGoals User {self.user_id}>'
    
    def to_dict(self):
        """Convert wellness goals to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'daily_blinks': self.daily_blinks,
            'screen_breaks': self.screen_breaks,
            'max_screen_time': self.max_screen_time,
            'blink_rate_target': self.blink_rate_target,
            'break_duration': self.break_duration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PerformanceMetrics(db.Model):
    """Performance metrics model for system monitoring"""
    __tablename__ = 'performance_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    device_id = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.Float, nullable=False)  # Unix timestamp
    cpu_percent = db.Column(db.Float, nullable=True)
    memory_mb = db.Column(db.Float, nullable=True)
    memory_percent = db.Column(db.Float, nullable=True)
    energy_impact = db.Column(db.String(20), nullable=True)  # Low, Medium, High
    battery_percent = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    def __repr__(self):
        return f'<PerformanceMetrics {self.id} - User {self.user_id}>'
    
    def to_dict(self):
        """Convert performance metrics to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'device_id': self.device_id,
            'timestamp': self.timestamp,
            'cpu_percent': self.cpu_percent,
            'memory_mb': self.memory_mb,
            'memory_percent': self.memory_percent,
            'energy_impact': self.energy_impact,
            'battery_percent': self.battery_percent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Notification(db.Model):
    """Notification model for user alerts and reminders"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # warning, info, success, error
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    action_url = db.Column(db.String(500), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    def __repr__(self):
        return f'<Notification {self.id} - User {self.user_id}>'
    
    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'read': self.read,
            'action_url': self.action_url,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AnalyticsData(db.Model):
    """Analytics data model for aggregated insights"""
    __tablename__ = 'analytics_data'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_blinks = db.Column(db.Integer, default=0)
    avg_blink_rate = db.Column(db.Float, default=0.0)
    screen_time_hours = db.Column(db.Float, default=0.0)
    wellness_score = db.Column(db.Float, default=0.0)
    goal_compliance = db.Column(db.Float, default=0.0)  # percentage
    breaks_taken = db.Column(db.Integer, default=0)
    eye_strain_level = db.Column(db.String(20), default='low')  # low, medium, high
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='_user_date_uc'),)
    
    def __repr__(self):
        return f'<AnalyticsData {self.id} - User {self.user_id} - {self.date}>'
    
    def to_dict(self):
        """Convert analytics data to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat() if self.date else None,
            'total_blinks': self.total_blinks,
            'avg_blink_rate': self.avg_blink_rate,
            'screen_time_hours': self.screen_time_hours,
            'wellness_score': self.wellness_score,
            'goal_compliance': self.goal_compliance,
            'breaks_taken': self.breaks_taken,
            'eye_strain_level': self.eye_strain_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 
