"""
Enhanced Eye Tracking Module with Camera Integration
Real-time blink detection and wellness monitoring
"""

import cv2
import time
import logging
import numpy as np
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path

logger = logging.getLogger(__name__)

class EnhancedEyeTrackingWorker(QThread):
    """Enhanced eye tracking with real camera integration"""
    
    # Signals
    blink_detected = pyqtSignal(int)  # Total blink count
    blink_rate_updated = pyqtSignal(float)  # Blinks per minute
    low_blink_warning = pyqtSignal()
    camera_error = pyqtSignal(str)
    session_data = pyqtSignal(dict)  # Complete session data
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.blink_count = 0
        self.last_blink_time = 0
        self.session_start = None
        self.blink_threshold = 15  # blinks per minute
        self.warning_interval = 60  # seconds between warnings
        self.last_warning_time = 0
        
        # OpenCV components
        self.cap = None
        self.face_cascade = None
        self.eye_cascade = None
        
        # Blink detection parameters
        self.eye_aspect_ratio_threshold = 0.25
        self.consecutive_frames_threshold = 3
        self.consecutive_frames = 0
        self.is_blinking = False
        
        # Load cascade files
        self._load_cascades()
    
    def _load_cascades(self):
        """Load OpenCV cascade classifiers"""
        try:
            # Try to load cascade files from various locations
            cascade_paths = [
                'cascades/',
                'data/cascades/',
                cv2.data.haarcascades,
                Path(__file__).parent / 'cascades'
            ]
            
            face_cascade_found = False
            eye_cascade_found = False
            
            for path in cascade_paths:
                if not face_cascade_found:
                    face_path = Path(path) / 'haarcascade_frontalface_alt.xml'
                    if face_path.exists():
                        self.face_cascade = cv2.CascadeClassifier(str(face_path))
                        face_cascade_found = True
                        logger.info(f"Face cascade loaded from {face_path}")
                
                if not eye_cascade_found:
                    eye_path = Path(path) / 'haarcascade_eye.xml'
                    if eye_path.exists():
                        self.eye_cascade = cv2.CascadeClassifier(str(eye_path))
                        eye_cascade_found = True
                        logger.info(f"Eye cascade loaded from {eye_path}")
            
            # Fallback to default OpenCV cascades
            if not face_cascade_found:
                face_cascade_file = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                self.face_cascade = cv2.CascadeClassifier(face_cascade_file)
                logger.info("Using default face cascade")
            
            if not eye_cascade_found:
                eye_cascade_file = cv2.data.haarcascades + 'haarcascade_eye.xml'
                self.eye_cascade = cv2.CascadeClassifier(eye_cascade_file)
                logger.info("Using default eye cascade")
                
        except Exception as e:
            logger.error(f"Failed to load cascades: {e}")
            self.face_cascade = cv2.CascadeClassifier()
            self.eye_cascade = cv2.CascadeClassifier()
    
    def _calculate_eye_aspect_ratio(self, eye_region):
        """Calculate eye aspect ratio for blink detection"""
        try:
            # Simple approximation using eye region dimensions
            height, width = eye_region.shape[:2]
            if width == 0:
                return 0.0
            return height / width
        except:
            return 0.0
    
    def _detect_blink(self, frame):
        """Detect blinks in the current frame"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))
            
            for (x, y, w, h) in faces:
                # Draw face rectangle
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                
                # Region of interest for eyes
                roi_gray = gray[y:y + h, x:x + w]
                roi_color = frame[y:y + h, x:x + w]
                
                # Detect eyes
                eyes = self.eye_cascade.detectMultiScale(roi_gray, 1.1, 3, minSize=(20, 20))
                
                if len(eyes) >= 2:
                    # Calculate average eye aspect ratio
                    total_ear = 0.0
                    valid_eyes = 0
                    
                    for (ex, ey, ew, eh) in eyes[:2]:  # Only use first two eyes
                        # Draw eye rectangle
                        cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
                        
                        # Extract eye region
                        eye_region = roi_gray[ey:ey + eh, ex:ex + ew]
                        ear = self._calculate_eye_aspect_ratio(eye_region)
                        
                        if ear > 0:
                            total_ear += ear
                            valid_eyes += 1
                    
                    if valid_eyes > 0:
                        avg_ear = total_ear / valid_eyes
                        
                        # Blink detection logic
                        if avg_ear < self.eye_aspect_ratio_threshold:
                            self.consecutive_frames += 1
                        else:
                            if self.consecutive_frames >= self.consecutive_frames_threshold and not self.is_blinking:
                                # Blink detected
                                self.blink_count += 1
                                self.is_blinking = True
                                self.last_blink_time = time.time()
                                
                                # Emit blink signal
                                self.blink_detected.emit(self.blink_count)
                                logger.debug(f"Blink detected! Total: {self.blink_count}")
                                
                            self.consecutive_frames = 0
                            self.is_blinking = False
                        
                        # Display EAR value
                        cv2.putText(frame, f"EAR: {avg_ear:.3f}", (10, 30), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        
                        return True  # Face and eyes detected
            
            return False  # No face or insufficient eyes detected
            
        except Exception as e:
            logger.error(f"Blink detection error: {e}")
            return False
    
    def _calculate_blink_rate(self):
        """Calculate current blink rate per minute"""
        if not self.session_start:
            return 0.0
        
        elapsed_time = time.time() - self.session_start
        if elapsed_time < 1:  # Avoid division by zero
            return 0.0
        
        blink_rate = (self.blink_count / elapsed_time) * 60.0
        return blink_rate
    
    def _check_low_blink_rate(self):
        """Check for low blink rate and emit warning if needed"""
        current_time = time.time()
        
        # Only check after at least 30 seconds of tracking
        if not self.session_start or (current_time - self.session_start) < 30:
            return
        
        blink_rate = self._calculate_blink_rate()
        
        # Check if warning is needed and enough time has passed since last warning
        if (blink_rate < self.blink_threshold and 
            (current_time - self.last_warning_time) > self.warning_interval):
            
            self.low_blink_warning.emit()
            self.last_warning_time = current_time
            logger.warning(f"Low blink rate detected: {blink_rate:.1f} bpm")
    
    def _add_status_overlay(self, frame):
        """Add status information overlay to frame"""
        try:
            # Calculate current stats
            current_time = time.time()
            elapsed_time = current_time - self.session_start if self.session_start else 0
            blink_rate = self._calculate_blink_rate()
            
            # Status text
            status_lines = [
                f"Blinks: {self.blink_count}",
                f"Rate: {blink_rate:.1f} bpm",
                f"Time: {int(elapsed_time)}s",
                f"Threshold: {self.blink_threshold} bpm"
            ]
            
            # Add status text to frame
            y_offset = 60
            for line in status_lines:
                cv2.putText(frame, line, (10, y_offset), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                y_offset += 25
            
            # Warning indicator
            if blink_rate < self.blink_threshold and elapsed_time > 30:
                cv2.putText(frame, "LOW BLINK RATE - TAKE A BREAK!", 
                          (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 
                          0.7, (0, 0, 255), 2)
                
        except Exception as e:
            logger.error(f"Overlay error: {e}")
    
    def run(self):
        """Main tracking loop"""
        try:
            # Initialize camera
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.camera_error.emit("Could not open camera")
                return
            
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.running = True
            self.session_start = time.time()
            self.blink_count = 0
            
            logger.info("Eye tracking started")
            
            frame_count = 0
            last_rate_update = time.time()
            
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    self.camera_error.emit("Failed to read from camera")
                    break
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Detect blinks
                self._detect_blink(frame)
                
                # Add status overlay
                self._add_status_overlay(frame)
                
                # Check for low blink rate periodically
                if frame_count % 30 == 0:  # Check every 30 frames
                    self._check_low_blink_rate()
                
                # Update blink rate every 5 seconds
                current_time = time.time()
                if current_time - last_rate_update >= 5.0:
                    blink_rate = self._calculate_blink_rate()
                    self.blink_rate_updated.emit(blink_rate)
                    last_rate_update = current_time
                
                # Show frame (optional - can be disabled for headless operation)
                cv2.imshow('WellnessAI Eye Tracker', frame)
                
                # Check for exit signal
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                frame_count += 1
                
                # Small delay to prevent excessive CPU usage
                self.msleep(33)  # ~30 FPS
            
            # Emit final session data
            session_data = {
                'session_id': str(int(self.session_start)),
                'total_blinks': self.blink_count,
                'blink_rate': self._calculate_blink_rate(),
                'duration_seconds': int(time.time() - self.session_start),
                'timestamp': datetime.now().isoformat()
            }
            self.session_data.emit(session_data)
            
        except Exception as e:
            logger.error(f"Eye tracking error: {e}")
            self.camera_error.emit(f"Tracking error: {e}")
        
        finally:
            # Cleanup
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows()
            logger.info("Eye tracking stopped")
    
    def stop(self):
        """Stop the eye tracking"""
        self.running = False
