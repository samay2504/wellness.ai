#!/usr/bin/env python3
"""
Production Eye Tracker UI Module for Wellness at Work Desktop Application
Production-ready UI wrapper with comprehensive error handling and monitoring
"""

import logging
import time
from typing import Optional, Callable, Any, Dict
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QProgressBar, QFrame, QGridLayout, QGroupBox)
from PyQt6.QtCore import QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPixmap, QPalette, QColor

import time
from desktop_app.eye_tracker import create_eye_tracker, BlinkData, ProductionEyeTracker

logger = logging.getLogger(__name__)

class EyeTrackerUI(QWidget):
    """Production-ready UI wrapper for eye tracker"""
    
    # Signals for production monitoring
    tracking_started = pyqtSignal()
    tracking_stopped = pyqtSignal()
    blink_detected = pyqtSignal(object)
    blink_count_updated = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    performance_metrics_updated = pyqtSignal(dict)
    camera_status_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Production state management
        self.eye_tracker: Optional[ProductionEyeTracker] = None
        self.is_running = False
        self.is_initialized = False
        self.camera_available = False
        self.error_count = 0
        self.session_start_time = None
        
        # Performance tracking
        self.frame_count = 0
        self.detection_rate = 0.0
        self.avg_processing_time = 0.0
        
        # UI components
        self.status_label: Optional[QLabel] = None
        self.blink_count_label: Optional[QLabel] = None
        self.camera_status_label: Optional[QLabel] = None
        self.performance_label: Optional[QLabel] = None
        self.start_button: Optional[QPushButton] = None
        self.stop_button: Optional[QPushButton] = None
        self.reset_button: Optional[QPushButton] = None
        
        # Monitoring timers
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self._health_check)
        
        # Initialize production components
        self._setup_production_ui()
        self._initialize_tracker()
        
        logger.info("Production EyeTrackerUI initialized")
    
    def _setup_production_ui(self):
        """Setup production-grade user interface"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Header section
        header_group = QGroupBox("Eye Tracking System")
        header_layout = QGridLayout()
        
        # Status indicators
        self.status_label = QLabel("Status: Initializing...")
        self.status_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        header_layout.addWidget(QLabel("System:"), 0, 0)
        header_layout.addWidget(self.status_label, 0, 1)
        
        self.camera_status_label = QLabel("Camera: Unknown")
        header_layout.addWidget(QLabel("Camera:"), 1, 0)
        header_layout.addWidget(self.camera_status_label, 1, 1)
        
        # Metrics display
        self.blink_count_label = QLabel("Blinks: 0")
        self.blink_count_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(QLabel("Count:"), 2, 0)
        header_layout.addWidget(self.blink_count_label, 2, 1)
        
        self.performance_label = QLabel("Performance: OK")
        header_layout.addWidget(QLabel("Performance:"), 3, 0)
        header_layout.addWidget(self.performance_label, 3, 1)
        
        header_group.setLayout(header_layout)
        layout.addWidget(header_group)
        
        # Control section
        control_group = QGroupBox("Controls")
        control_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Tracking")
        self.start_button.clicked.connect(self.start_tracking)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #2ECC71;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #27AE60; }
            QPushButton:disabled { background-color: #95A5A6; }
        """)
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Tracking")
        self.stop_button.clicked.connect(self.stop_tracking)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #C0392B; }
            QPushButton:disabled { background-color: #95A5A6; }
        """)
        control_layout.addWidget(self.stop_button)
        
        self.reset_button = QPushButton("Reset Session")
        self.reset_button.clicked.connect(self.reset_session)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #F39C12;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #E67E22; }
        """)
        control_layout.addWidget(self.reset_button)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        self.setLayout(layout)
        self.setMinimumSize(400, 300)
    
    def _initialize_tracker(self):
        """Initialize production eye tracker with comprehensive error handling"""
        try:
            self.eye_tracker = create_eye_tracker(
                show_preview=False,
                ear_threshold=0.23,
                consec_frames=3,
                detection_confidence=0.7,
                tracking_confidence=0.5
            )
            
            # Setup production callbacks
            self.eye_tracker.add_blink_callback(self._on_blink_detected)
            self.eye_tracker.add_error_callback(self._on_error)
            
            self.is_initialized = True
            self.status_label.setText("Status: Ready")
            self.camera_status_label.setText("Camera: Ready")
            self.start_button.setEnabled(True)
            
            # Start health monitoring
            self.health_timer.start(5000)  # Check health every 5 seconds
            
            logger.info("Production eye tracker initialized successfully")
            
        except Exception as e:
            self.error_count += 1
            error_msg = f"Initialization failed: {str(e)}"
            logger.error(error_msg)
            
            self.status_label.setText("Status: Error")
            self.camera_status_label.setText("Camera: Error")
            self.start_button.setEnabled(False)
            self.error_occurred.emit(error_msg)
    
    def start_tracking(self) -> bool:
        """Start production eye tracking with comprehensive monitoring"""
        if not self.is_initialized:
            self._initialize_tracker()
            if not self.is_initialized:
                return False
        
        try:
            success = self.eye_tracker.start_tracking()
            
            if success:
                self.is_running = True
                self.camera_available = True
                self.session_start_time = time.time()
                
                # Update UI
                self.status_label.setText("Status: Active")
                self.camera_status_label.setText("Camera: Active")
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                
                # Start monitoring timers
                self.update_timer.start(1000)  # Update UI every second
                
                # Emit signals
                self.tracking_started.emit()
                self.status_updated.emit("tracking_started")
                self.camera_status_changed.emit(True)
                
                logger.info("Production eye tracking started successfully")
                return True
            else:
                self.error_count += 1
                error_msg = "Failed to start camera or tracking system"
                self.status_label.setText("Status: Camera Error")
                self.camera_status_label.setText("Camera: Failed")
                self.error_occurred.emit(error_msg)
                return False
                
        except Exception as e:
            self.error_count += 1
            error_msg = f"Tracking start error: {str(e)}"
            logger.error(error_msg)
            
            self.status_label.setText("Status: Error")
            self.error_occurred.emit(error_msg)
            return False
    
    def stop_tracking(self) -> bool:
        """Stop production eye tracking with cleanup"""
        try:
            if self.eye_tracker:
                self.eye_tracker.stop_tracking()
            
            self.is_running = False
            self.camera_available = False
            
            # Update UI
            self.status_label.setText("Status: Stopped")
            self.camera_status_label.setText("Camera: Stopped")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            
            # Stop timers
            self.update_timer.stop()
            
            # Emit signals
            self.tracking_stopped.emit()
            self.status_updated.emit("tracking_stopped")
            self.camera_status_changed.emit(False)
            
            logger.info("Production eye tracking stopped")
            return True
            
        except Exception as e:
            error_msg = f"Error stopping tracking: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def _on_blink_detected(self, blink_data: BlinkData):
        """Handle production blink detection with monitoring"""
        try:
            self.frame_count += 1
            
            # Update UI
            count = self.get_current_blink_count()
            self.blink_count_label.setText(f"Blinks: {count}")
            
            # Emit production signals
            self.blink_detected.emit(blink_data)
            self.blink_count_updated.emit(count)
            
            # Update performance metrics
            self._update_performance_metrics()
            
            logger.debug(f"Production blink detected: count={count}")
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error in blink detection handler: {e}")
    
    def _on_error(self, error: Exception):
        """Handle production errors with recovery attempts"""
        self.error_count += 1
        error_msg = str(error)
        logger.error(f"Production eye tracker error: {error_msg}")
        
        # Update UI status
        self.status_label.setText("Status: Error")
        if "camera" in error_msg.lower():
            self.camera_status_label.setText("Camera: Error")
            self.camera_available = False
            self.camera_status_changed.emit(False)
        
        # Attempt recovery for certain errors
        if self.error_count < 3 and "camera" in error_msg.lower():
            logger.info("Attempting camera recovery...")
            self._attempt_camera_recovery()
        
        self.error_occurred.emit(error_msg)
    
    def _attempt_camera_recovery(self):
        """Attempt to recover from camera errors"""
        try:
            if self.is_running:
                self.stop_tracking()
            
            # Wait before retry
            QTimer.singleShot(2000, lambda: self.start_tracking() if not self.is_running else None)
            
        except Exception as e:
            logger.error(f"Camera recovery failed: {e}")
    
    def _update_display(self):
        """Update production UI display"""
        if not self.is_running:
            return
        
        try:
            # Update blink count
            count = self.get_current_blink_count()
            self.blink_count_label.setText(f"Blinks: {count}")
            
            # Update performance metrics
            self._update_performance_metrics()
            
        except Exception as e:
            logger.error(f"Error updating display: {e}")
    
    def _update_performance_metrics(self):
        """Update production performance metrics"""
        try:
            if self.eye_tracker and hasattr(self.eye_tracker, 'get_stats'):
                stats = self.eye_tracker.get_stats()
                
                performance_data = {
                    'frame_count': self.frame_count,
                    'detection_rate': stats.get('detection_rate', 0.0),
                    'error_count': self.error_count,
                    'session_duration': time.time() - self.session_start_time if self.session_start_time else 0
                }
                
                self.performance_label.setText(
                    f"FPS: {stats.get('fps', 0):.1f} | "
                    f"Rate: {performance_data['detection_rate']:.1f}% | "
                    f"Errors: {self.error_count}"
                )
                
                self.performance_metrics_updated.emit(performance_data)
                
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    def _health_check(self):
        """Perform production health checks"""
        try:
            if self.is_running and self.eye_tracker:
                # Check if tracker is still responsive
                if hasattr(self.eye_tracker, 'is_healthy'):
                    if not self.eye_tracker.is_healthy():
                        logger.warning("Eye tracker health check failed")
                        self._attempt_camera_recovery()
                
                # Check error rate
                if self.error_count > 10:
                    logger.warning(f"High error count detected: {self.error_count}")
                    self.status_label.setText("Status: High Error Rate")
                
        except Exception as e:
            logger.error(f"Health check error: {e}")
    
    def get_current_blink_count(self) -> int:
        """Get current production blink count"""
        if self.eye_tracker and hasattr(self.eye_tracker, 'get_current_blink_count'):
            return self.eye_tracker.get_current_blink_count()
        return 0
    
    def get_production_stats(self) -> Dict[str, Any]:
        """Get comprehensive production statistics"""
        base_stats = {
            "is_running": self.is_running,
            "is_initialized": self.is_initialized,
            "camera_available": self.camera_available,
            "error_count": self.error_count,
            "frame_count": self.frame_count,
            "blink_count": self.get_current_blink_count()
        }
        
        if self.eye_tracker and hasattr(self.eye_tracker, 'get_stats'):
            tracker_stats = self.eye_tracker.get_stats()
            base_stats.update(tracker_stats)
        
        return base_stats
    
    def reset_session(self):
        """Reset production tracking session"""
        try:
            was_running = self.is_running
            
            if was_running:
                self.stop_tracking()
            
            if self.eye_tracker and hasattr(self.eye_tracker, 'reset_session'):
                self.eye_tracker.reset_session()
            
            # Reset UI
            self.blink_count_label.setText("Blinks: 0")
            self.error_count = 0
            self.frame_count = 0
            self.session_start_time = None
            
            if was_running:
                self.start_tracking()
                
            logger.info("Production session reset completed")
            
        except Exception as e:
            logger.error(f"Error resetting session: {e}")
            self.error_occurred.emit(str(e))
    
    def add_blink_callback(self, callback: Callable[[BlinkData], None]):
        """Add production blink callback"""
        if self.eye_tracker:
            self.eye_tracker.add_blink_callback(callback)
    
    def add_error_callback(self, callback: Callable[[Exception], None]):
        """Add production error callback"""
        if self.eye_tracker:
            self.eye_tracker.add_error_callback(callback)
    
    def is_tracking_active(self) -> bool:
        """Check if production tracking is active"""
        return self.is_running and self.camera_available
    
    def cleanup(self):
        """Production cleanup with comprehensive resource management"""
        try:
            logger.info("Starting production cleanup...")
            
            # Stop all timers
            self.update_timer.stop()
            self.health_timer.stop()
            
            # Stop tracking
            if self.is_running:
                self.stop_tracking()
            
            # Cleanup eye tracker
            if self.eye_tracker and hasattr(self.eye_tracker, 'cleanup'):
                self.eye_tracker.cleanup()
            
            logger.info("Production cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"Error during production cleanup: {e}")
    
    def closeEvent(self, event):
        """Handle production widget close event"""
        self.cleanup()
        super().closeEvent(event)
