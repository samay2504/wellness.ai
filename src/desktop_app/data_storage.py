"""
Enhanced Data Storage Module for Wellness at Work
Handles both SQLite and JSON session-based storage matching the required format
"""

import os
import json
import sqlite3
import logging
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class BlinkEvent:
    """Enhanced blink event for session tracking"""
    id: str
    user_id: str
    timestamp: float
    count: int
    session_id: str
    device_id: str = "desktop"
    created_at: str = ""
    open_closed: str = "open"  # Changed default to match example
    direction: str = "left"     # Changed default to match example
    confidence: float = 0.0     # Changed default to match example
    ear_left: Optional[float] = None
    ear_right: Optional[float] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlinkEvent':
        """Create from dictionary"""
        return cls(**data)


@dataclass 
class SessionMetadata:
    """Session metadata structure"""
    session_id: str
    user_id: str
    device_id: str
    created_at: str
    

class SessionDataStorage:
    """Enhanced data storage with SQLite persistence and JSON session files"""
    
    def __init__(self, db_path: str = "data/local.db", 
                 json_base_path: str = "data/eye_tracking"):
        self.db_path = Path(db_path)
        self.json_base_path = Path(json_base_path)
        
        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.json_base_path.mkdir(parents=True, exist_ok=True)
        
        # Current session tracking
        self.current_session_id = None
        self.current_user_id = None
        self.current_device_id = str(uuid.uuid4())[:8]
        self.session_start_time = None
        self.session_events = []
        
        # Initialize database
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database with proper schema"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()
            
            # Create enhanced blink_events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blink_events (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    count INTEGER NOT NULL,
                    session_id TEXT NOT NULL,
                    device_id TEXT NOT NULL DEFAULT 'desktop',
                    created_at TEXT,
                    open_closed TEXT DEFAULT 'open',
                    direction TEXT DEFAULT 'left',
                    confidence REAL DEFAULT 0.0,
                    ear_left REAL,
                    ear_right REAL,
                    synced INTEGER DEFAULT 0
                )
            """)
            
            # Migrate existing table if needed
            self._migrate_blink_events_table(cursor)
            
            # Create sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    created_at TEXT,
                    start_time REAL NOT NULL,
                    end_time REAL,
                    total_events INTEGER DEFAULT 0,
                    json_file_path TEXT
                )
            """)
            
            # Migrate sessions table if needed
            self._migrate_sessions_table(cursor)
            
            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_blink_events_session 
                ON blink_events(session_id, timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_blink_events_user 
                ON blink_events(user_id, timestamp)
            """)
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _migrate_blink_events_table(self, cursor):
        """Migrate existing blink_events table to new schema"""
        try:
            # Check existing columns
            cursor.execute("PRAGMA table_info(blink_events)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            # Add missing columns
            if 'created_at' not in existing_columns:
                cursor.execute("ALTER TABLE blink_events ADD COLUMN created_at TEXT")
                # Update existing rows with created_at based on timestamp
                cursor.execute("""
                    UPDATE blink_events 
                    SET created_at = datetime(timestamp, 'unixepoch') 
                    WHERE created_at IS NULL
                """)
            
            logger.info("Blink events table migrated successfully")
            
        except Exception as e:
            logger.warning(f"Failed to migrate blink_events table: {e}")
    
    def _migrate_sessions_table(self, cursor):
        """Migrate existing sessions table to new schema"""
        try:
            # Check if sessions table exists and get its columns
            cursor.execute("PRAGMA table_info(sessions)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            # Add missing columns to sessions table
            if 'end_time' not in existing_columns:
                cursor.execute("ALTER TABLE sessions ADD COLUMN end_time REAL")
            
            if 'total_events' not in existing_columns:
                cursor.execute("ALTER TABLE sessions ADD COLUMN total_events INTEGER DEFAULT 0")
            
            if 'json_file_path' not in existing_columns:
                cursor.execute("ALTER TABLE sessions ADD COLUMN json_file_path TEXT")
            
            if 'created_at' not in existing_columns:
                cursor.execute("ALTER TABLE sessions ADD COLUMN created_at TEXT")
                # Update existing rows
                cursor.execute("""
                    UPDATE sessions 
                    SET created_at = datetime(start_time, 'unixepoch') 
                    WHERE created_at IS NULL
                """)
            
            logger.info("Sessions table migrated successfully")
            
        except Exception as e:
            logger.warning(f"Failed to migrate sessions table: {e}")
    
    def start_session(self, user_id: str) -> str:
        """Start a new blink tracking session"""
        # End current session if exists
        if self.current_session_id:
            self.end_session()
        
        # Create new session
        self.current_session_id = f"session_{int(time.time())}"
        self.current_user_id = user_id
        self.current_device_id = str(uuid.uuid4())[:8]
        self.session_start_time = time.time()
        self.session_events = []
        
        # Save session to database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            created_at = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO sessions (session_id, user_id, device_id, created_at, start_time)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.current_session_id,
                self.current_user_id, 
                self.current_device_id,
                created_at,
                self.session_start_time
            ))
            conn.commit()
            conn.close()
            
            logger.info(f"Started new session: {self.current_session_id}")
            return self.current_session_id
            
        except Exception as e:
            logger.error(f"Failed to save session to database: {e}")
            return self.current_session_id
    
    def save_blink_event(self, blink_count: int, 
                        direction: str = "left",
                        confidence: float = 0.0,
                        ear_left: Optional[float] = None,
                        ear_right: Optional[float] = None) -> bool:
        """Save a blink event to both SQLite and session data"""
        if not self.current_session_id or not self.current_user_id:
            logger.warning("No active session - starting default session")
            self.start_session("anonymous")
        
        try:
            # Create blink event
            event = BlinkEvent(
                id=str(uuid.uuid4()),
                user_id=self.current_user_id,
                timestamp=time.time(),
                count=blink_count,
                session_id=self.current_session_id,
                device_id=self.current_device_id,
                created_at=datetime.now().isoformat(),
                open_closed="open",
                direction=direction,
                confidence=confidence,
                ear_left=ear_left,
                ear_right=ear_right
            )
            
            # Save to SQLite
            self._save_to_sqlite(event)
            
            # Add to session events
            self.session_events.append(event)
            
            logger.debug(f"Saved blink event: {event.id} (count: {event.count})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save blink event: {e}")
            return False
    
    def _save_to_sqlite(self, event: BlinkEvent):
        """Save event to SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ensure created_at is set
            created_at = event.created_at if event.created_at else datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO blink_events 
                (id, user_id, timestamp, count, session_id, device_id, 
                 created_at, open_closed, direction, confidence, ear_left, ear_right, synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                event.id, event.user_id, event.timestamp, event.count,
                event.session_id, event.device_id, created_at,
                event.open_closed, event.direction, event.confidence,
                event.ear_left, event.ear_right
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save to SQLite: {e}")
            raise
    
    def end_session(self) -> Optional[str]:
        """End current session and save JSON file"""
        if not self.current_session_id:
            return None
        
        try:
            # Update session in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            end_time = time.time()
            total_events = len(self.session_events)
            
            # Create JSON filename
            session_date = datetime.now().strftime("%Y%m%d_%H")
            json_filename = f"blink_session_{self.current_session_id}_{session_date}.json"
            json_path = self.json_base_path / json_filename
            
            # Update session record
            cursor.execute("""
                UPDATE sessions 
                SET end_time = ?, total_events = ?, json_file_path = ?
                WHERE session_id = ?
            """, (end_time, total_events, str(json_path), self.current_session_id))
            
            conn.commit()
            conn.close()
            
            # Save JSON session file
            self._save_session_json(json_path)
            
            session_id = self.current_session_id
            
            # Reset session tracking
            self.current_session_id = None
            self.current_user_id = None
            self.session_start_time = None
            self.session_events = []
            
            logger.info(f"Session ended: {session_id}, saved to {json_filename}")
            return str(json_path)
            
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
            return None
    
    def _save_session_json(self, json_path: Path):
        """Save session data to JSON file matching the required format"""
        try:
            # Create session metadata
            session_metadata = SessionMetadata(
                session_id=self.current_session_id,
                user_id=self.current_user_id,
                device_id=self.current_device_id,
                created_at=datetime.fromtimestamp(self.session_start_time).isoformat() if self.session_start_time else datetime.now().isoformat()
            )
            
            # Create the session data structure matching the example
            session_data = {
                "events": [event.to_dict() for event in self.session_events],
                "session_metadata": asdict(session_metadata),
                "last_updated": datetime.now().isoformat(),
                "event_count": len(self.session_events)
            }
            
            # Write to JSON file
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Session JSON saved: {json_path} with {len(self.session_events)} events")
            
        except Exception as e:
            logger.error(f"Failed to save session JSON: {e}")
            raise
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all session records from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT session_id, user_id, device_id, created_at, 
                       start_time, end_time, total_events, json_file_path
                FROM sessions ORDER BY start_time DESC
            """)
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "session_id": row[0],
                    "user_id": row[1], 
                    "device_id": row[2],
                    "created_at": row[3],
                    "start_time": row[4],
                    "end_time": row[5],
                    "total_events": row[6],
                    "json_file_path": row[7]
                })
            
            conn.close()
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get sessions: {e}")
            return []
    
    def get_session_events(self, session_id: str) -> List[BlinkEvent]:
        """Get all events for a specific session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, user_id, timestamp, count, session_id, device_id,
                       created_at, open_closed, direction, confidence, ear_left, ear_right
                FROM blink_events WHERE session_id = ? ORDER BY timestamp
            """, (session_id,))
            
            events = []
            for row in cursor.fetchall():
                events.append(BlinkEvent(
                    id=row[0], user_id=row[1], timestamp=row[2], count=row[3],
                    session_id=row[4], device_id=row[5], created_at=row[6],
                    open_closed=row[7], direction=row[8], confidence=row[9],
                    ear_left=row[10], ear_right=row[11]
                ))
            
            conn.close()
            return events
            
        except Exception as e:
            logger.error(f"Failed to get session events: {e}")
            return []

    def export_session_to_json(self, session_id: str, output_path: Optional[str] = None) -> Optional[str]:
        """Export a specific session to JSON format"""
        try:
            # Get session data
            sessions = self.get_all_sessions()
            session_info = next((s for s in sessions if s["session_id"] == session_id), None)
            
            if not session_info:
                logger.error(f"Session not found: {session_id}")
                return None
            
            events = self.get_session_events(session_id)
            
            # Create output path if not provided
            if not output_path:
                session_date = datetime.now().strftime("%Y%m%d_%H")
                filename = f"blink_session_{session_id}_{session_date}.json"
                output_path = self.json_base_path / filename
            
            # Create session metadata
            session_metadata = {
                "session_id": session_info["session_id"],
                "user_id": session_info["user_id"],
                "device_id": session_info["device_id"],
                "created_at": session_info["created_at"]
            }
            
            # Create the session data structure
            session_data = {
                "events": [event.to_dict() for event in events],
                "session_metadata": session_metadata,
                "last_updated": datetime.now().isoformat(),
                "event_count": len(events)
            }
            
            # Write to JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Session exported to JSON: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to export session to JSON: {e}")
            return None
