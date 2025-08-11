"""
Enhanced eye tracking module for Wellness at Work
Integrates MediaPipe face detection with blink counting and local fallbacks
"""

import cv2
import mediapipe as mp
import numpy as np
import logging
import uuid
import time
import os
import json
import threading
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from PyQt6.QtCore import QThread, pyqtSignal, QTimer

logger = logging.getLogger(__name__)

# Eye landmark indices for left and right eyes (from MediaPipe Face Mesh)
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# Default values for blink detection
DEFAULT_EAR_THRESH = 0.21
DEFAULT_CONSEC_FRAMES = 2
DEFAULT_CAMERA_ID = 0

# Local storage path for backup
LOCAL_STORAGE_DIR = Path("data") / "eye_tracking"


class EyeState(Enum):
    """Eye state enumeration"""
    OPEN = "open"
    CLOSED = "closed"
    BLINKING = "blinking"
    UNKNOWN = "unknown"


@dataclass
class BlinkEvent:
    """Represents a blink event with metadata"""
    timestamp: float
    count: int
    duration: float
    confidence: float
    session_id: str
    device_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlinkEvent':
        """Create from dictionary"""
        return cls(**data)


class EyeTracker(QThread):
    """Enhanced eye tracker with local fallbacks and improved error handling"""
    
    # Signals
    blink_count_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    fps_updated = pyqtSignal(float)
    frame_processed = pyqtSignal(object)  # For UI preview
    
    def __init__(self, 
                 camera_id: int = DEFAULT_CAMERA_ID,
                 ear_threshold: float = DEFAULT_EAR_THRESH, 
                 consec_frames: int = DEFAULT_CONSEC_FRAMES,
                 use_local_storage: bool = True,
                 parent=None):
        super().__init__(parent)
        
        # Core tracking attributes
        self._running = False
        self._blink_count = 0
        self._frame_counter = 0
        self._ear_thresh = ear_threshold
        self._consec_frames = consec_frames
        self._camera_id = camera_id
        self._use_local_storage = use_local_storage
        self._ear_history = []  # Track EAR values for calibration
        self._fps = 0
        self._last_frame_time = 0
        self._frame_times = []  # For rolling FPS calculation
        
        # Hardware handles
        self._cap = None
        self._face_mesh = None
        
        # Session information
        self.session_id = self._generate_session_id()
        self.device_id = self._generate_device_id()
        self.start_time = time.time()
        
        # Backup and storage
        if use_local_storage:
            os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)
            
        # Events storage
        self._blink_events = []
        self._event_lock = threading.Lock()
        
    def run(self):
        """Main tracking loop"""
        self._running = True
        self._blink_count = 0
        self._frame_counter = 0
        self._blink_events = []
        self.start_time = time.time()
        self.status_updated.emit("Starting eye tracker...")
        
        # Initialize camera
        try:
            self._cap = cv2.VideoCapture(self._camera_id)
            if not self._cap.isOpened():
                self.error_occurred.emit(f"Failed to open camera {self._camera_id}")
                self._running = False
                return
        except Exception as e:
            self.error_occurred.emit(f"Camera error: {str(e)}")
            self._running = False
            return
            
        # Initialize MediaPipe
        try:
            mp_face_mesh = mp.solutions.face_mesh
            self._face_mesh = mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        except Exception as e:
            self.error_occurred.emit(f"MediaPipe initialization error: {str(e)}")
            if self._cap:
                self._cap.release()
            self._running = False
            return
            
        # Main processing loop
        self.status_updated.emit("Running")
        try:
            frame_count = 0
            start_time = time.time()
            
            while self._running:
                # Measure frame processing time
                frame_start = time.time()
                
                # Capture frame
                ret, frame = self._cap.read()
                if not ret:
                    self.error_occurred.emit("Failed to capture frame")
                    if frame_count > 10:  # Only break if we've processed some frames
                        self.msleep(100)
                        continue
                    else:
                        break
                        
                # Process frame
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self._face_mesh.process(rgb)
                
                # Track FPS
                frame_count += 1
                current_time = time.time()
                self._frame_times.append(current_time)
                
                # Limit fps history to last 30 frames
                if len(self._frame_times) > 30:
                    self._frame_times.pop(0)
                
                # Calculate FPS every 10 frames
                if frame_count % 10 == 0 and len(self._frame_times) > 1:
                    fps = len(self._frame_times) / (self._frame_times[-1] - self._frame_times[0])
                    self._fps = fps
                    self.fps_updated.emit(fps)
                
                # Detect face landmarks
                if results.multi_face_landmarks:
                    h, w, _ = frame.shape
                    for face_landmarks in results.multi_face_landmarks:
                        # Extract eye landmarks
                        left_eye = [(int(face_landmarks.landmark[i].x * w), 
                                     int(face_landmarks.landmark[i].y * h)) for i in LEFT_EYE]
                        right_eye = [(int(face_landmarks.landmark[i].x * w), 
                                      int(face_landmarks.landmark[i].y * h)) for i in RIGHT_EYE]
                        
                        # Calculate eye aspect ratios
                        left_ear = self.eye_aspect_ratio(left_eye)
                        right_ear = self.eye_aspect_ratio(right_eye)
                        ear = (left_ear + right_ear) / 2.0
                        
                        # Track EAR history for calibration
                        self._ear_history.append(ear)
                        if len(self._ear_history) > 300:  # Keep last 10 seconds at 30fps
                            self._ear_history.pop(0)
                        
                        # Detect blinks
                        if ear < self._ear_thresh:
                            self._frame_counter += 1
                        else:
                            if self._frame_counter >= self._consec_frames:
                                # Blink detected
                                self._blink_count += 1
                                
                                # Calculate blink duration and confidence
                                blink_duration = self._frame_counter / self._fps if self._fps > 0 else 0.1
                                confidence = self._calculate_confidence(self._ear_history)
                                
                                # Create blink event
                                blink_event = BlinkEvent(
                                    timestamp=current_time,
                                    count=self._blink_count,
                                    duration=blink_duration,
                                    confidence=confidence,
                                    session_id=self.session_id,
                                    device_id=self.device_id
                                )
                                
                                # Store event
                                with self._event_lock:
                                    self._blink_events.append(blink_event)
                                    
                                # Save to local storage if enabled
                                if self._use_local_storage:
                                    self._save_blink_event(blink_event)
                                    
                                # Emit signal
                                self.blink_count_updated.emit(self._blink_count)
                                
                            self._frame_counter = 0
                            
                # Emit frame for UI preview if needed
                self.frame_processed.emit(frame)
                
                # Maintain consistent timing
                frame_time = time.time() - frame_start
                if frame_time < 1/30:  # Cap at 30fps
                    self.msleep(int((1/30 - frame_time) * 1000))
                    
        except Exception as e:
            self.error_occurred.emit(f"Tracking error: {str(e)}")
            logger.exception("Error during eye tracking")
            
        finally:
            # Clean up
            if self._face_mesh:
                self._face_mesh.close()
                
            if self._cap:
                self._cap.release()
                
            self._running = False
            self.status_updated.emit("Stopped")

    def start(self, priority=QThread.Priority.InheritPriority):
        """Start tracking with specified priority"""
        if not self.isRunning():
            super().start(priority)

    def stop(self):
        """Stop tracking and clean up"""
        self._running = False
        self.wait()

    def is_running(self) -> bool:
        """Check if tracker is running"""
        return self._running

    def get_blink_count(self) -> int:
        """Get current blink count"""
        return self._blink_count
        
    def get_fps(self) -> float:
        """Get current FPS"""
        return self._fps

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current tracking statistics"""
        uptime = time.time() - self.start_time
        return {
            'blink_count': self._blink_count,
            'session_id': self.session_id,
            'device_id': self.device_id,
            'is_running': self._running,
            'uptime': uptime,
            'fps': self._fps,
            'blinks_per_minute': (self._blink_count / (uptime / 60)) if uptime > 0 else 0
        }

    def reset_session(self):
        """Reset session counters"""
        if not self._running:
            self._blink_count = 0
            self._frame_counter = 0
            self._blink_events = []
            self._ear_history = []
            self.session_id = self._generate_session_id()
            self.start_time = time.time()
        else:
            self.error_occurred.emit("Cannot reset while tracker is running")

    def export_data(self) -> List[BlinkEvent]:
        """Export blink data"""
        with self._event_lock:
            return self._blink_events.copy()
            
    def calibrate(self):
        """Auto-calibrate EAR threshold based on collected data"""
        if len(self._ear_history) > 50:  # Need sufficient data
            # Calculate average and standard deviation
            avg_ear = np.mean(self._ear_history)
            std_ear = np.std(self._ear_history)
            
            # Set threshold at 2 standard deviations below average
            # (assuming normal eye is open most of the time)
            new_thresh = max(0.15, avg_ear - (std_ear * 2))
            
            # Update threshold
            self._ear_thresh = new_thresh
            logger.info(f"Calibrated EAR threshold: {new_thresh}")
            return new_thresh
        else:
            logger.warning("Insufficient data for calibration")
            return self._ear_thresh
            
    def get_ear_threshold(self) -> float:
        """Get current EAR threshold"""
        return self._ear_thresh
        
    def set_ear_threshold(self, threshold: float):
        """Manually set EAR threshold"""
        if 0.1 <= threshold <= 0.5:  # Sanity check
            self._ear_thresh = threshold
            logger.info(f"EAR threshold set to: {threshold}")
        else:
            logger.warning(f"Invalid EAR threshold: {threshold}")

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"session_{int(time.time())}_{uuid.uuid4().hex[:8]}"

    def _generate_device_id(self) -> str:
        """Generate unique device ID"""
        # Try to get a persistent device ID
        device_file = LOCAL_STORAGE_DIR / "device_id.txt"
        
        if device_file.exists():
            try:
                with open(device_file, 'r') as f:
                    device_id = f.read().strip()
                    if device_id:
                        return device_id
            except Exception:
                pass
                
        # Generate new ID if not found
        device_id = f"device_{uuid.uuid4().hex[:12]}"
        
        # Save for future use
        try:
            os.makedirs(device_file.parent, exist_ok=True)
            with open(device_file, 'w') as f:
                f.write(device_id)
        except Exception:
            logger.exception("Failed to save device ID")
            
        return device_id

    def _calculate_confidence(self, ear_values: List[float]) -> float:
        """Calculate confidence based on EAR values"""
        if not ear_values or len(ear_values) < 2:
            return 0.5
            
        # Use variance as an indicator of confidence
        variance = np.var(ear_values[-10:])  # Use recent values
        
        # Low variance indicates more confidence
        confidence = max(0.0, min(1.0, 1.0 - (variance * 20)))
        return confidence

    @staticmethod
    def eye_aspect_ratio(eye_landmarks: List[Tuple[int, int]]) -> float:
        """Calculate Eye Aspect Ratio for given landmarks"""
        if len(eye_landmarks) != 6:
            return 0.0
            
        # Calculate distances between landmarks
        A = np.linalg.norm(np.array(eye_landmarks[1]) - np.array(eye_landmarks[5]))
        B = np.linalg.norm(np.array(eye_landmarks[2]) - np.array(eye_landmarks[4]))
        C = np.linalg.norm(np.array(eye_landmarks[0]) - np.array(eye_landmarks[3]))
        
        if C == 0:
            return 0.0
            
        return (A + B) / (2.0 * C)

    def _save_blink_event(self, event: BlinkEvent):
        """Save blink event to local storage"""
        try:
            session_file = LOCAL_STORAGE_DIR / f"blinks_{self.session_id}.json"
            
            # Create or append to file
            if session_file.exists():
                try:
                    with open(session_file, 'r') as f:
                        events = json.load(f)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    events = []
            else:
                events = []
                
            # Add new event
            events.append(event.to_dict())
            
            # Save file
            with open(session_file, 'w') as f:
                json.dump(events, f)
                
        except Exception as e:
            logger.exception(f"Failed to save blink event: {e}")

    def get_local_sessions(self) -> List[Dict[str, Any]]:
        """Get list of locally stored sessions"""
        sessions = []
        
        try:
            for file in LOCAL_STORAGE_DIR.glob("blinks_*.json"):
                session_id = file.stem.replace("blinks_", "")
                try:
                    with open(file, 'r') as f:
                        events = json.load(f)
                        if events:
                            first_event = events[0]
                            last_event = events[-1]
                            sessions.append({
                                'session_id': session_id,
                                'start_time': first_event.get('timestamp'),
                                'end_time': last_event.get('timestamp'),
                                'blink_count': len(events),
                                'file_path': str(file)
                            })
                except Exception:
                    logger.exception(f"Error reading session file: {file}")
                    
        except Exception:
            logger.exception("Error listing session files")
            
        return sessions

    def load_session(self, session_id: str) -> List[BlinkEvent]:
        """Load blink events from a specific session"""
        file_path = LOCAL_STORAGE_DIR / f"blinks_{session_id}.json"
        events = []
        
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        events.append(BlinkEvent.from_dict(item))
            except Exception:
                logger.exception(f"Error loading session: {session_id}")
                
        return events
