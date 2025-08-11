#!/usr/bin/env python3
"""
Wellness at Work Desktop Application - Production Version
Main entry point for the cross-platform eye tracker application with enhanced error handling
"""

import sys
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

# Ensure required directories exist
for directory in ["logs", "data", "data/eye_tracking"]:
    Path(directory).mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/wellness_ai.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    from desktop_app.auth import AuthManager
    from desktop_app.auth_ui import AuthDialog
    from desktop_app.ui import MainWindow
    from desktop_app.sync import SyncManager
    from desktop_app.eye_tracker_ui import EyeTrackerUI
    from desktop_app.eye_tracker import create_eye_tracker, BlinkData
    
    # Try to import metrics, use a mock if it fails
    try:
        from desktop_app.metrics import PerformanceMonitor
    except ImportError:
        logger.warning("PerformanceMonitor not available, using mock")
        class PerformanceMonitor:
            def __init__(self): pass
            def start(self): return True
            def stop(self): pass
            def get_current_metrics(self): return None
            
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


class WellnessAIApp:
    """Main application class for Wellness at Work with enhanced error handling"""
    
    def __init__(self):
        try:
            # Initialize Qt Application
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("Wellness at Work")
            self.app.setApplicationVersion("1.0.0")
            self.app.setOrganizationName("Wellness.ai")
            
            # Set application icon
            icon_path = Path(__file__).parent / "assets" / "icon.png"
            if icon_path.exists():
                self.app.setWindowIcon(QIcon(str(icon_path)))
            
            # Optional headless mode for CI or automated checks
            headless = os.environ.get('WELLNESS_HEADLESS', '0') == '1'

            # Show authentication dialog first (skip in headless)
            self.authenticated_user = None if headless else self._authenticate_user()
            if not headless and not self.authenticated_user:
                logger.info("Authentication cancelled or failed")
                sys.exit(0)
            
            # Initialize core components with error handling
            self._initialize_components()
            
            # Initialize UI (skip showing window in headless)
            self.main_window = MainWindow(
                auth_manager=self.auth_manager,
                performance_monitor=self.performance_monitor,
                sync_manager=self.sync_manager,
                eye_tracker=self.eye_tracker,
                eye_blink_tracker=self.blink_tracker,
                data_storage=self.data_storage
            )
            self._headless = headless
            
            logger.info("Wellness at Work application initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            self._show_error_dialog("Initialization Error", 
                                   f"Failed to initialize application: {e}\n\n"
                                   "Please check that:\n"
                                   "1. Camera is connected and not in use\n"
                                   "2. All dependencies are installed\n"
                                   "3. You have necessary permissions")
    
    def _authenticate_user(self):
        """Show authentication dialog and return authenticated user"""
        try:
            auth_dialog = AuthDialog()
            if auth_dialog.exec() == QDialog.DialogCode.Accepted:
                user = auth_dialog.get_authenticated_user()
                if user:
                    logger.info(f"User authenticated: {user.email if hasattr(user, 'email') else user.name}")
                    return user
            return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            self._show_error_dialog("Initialization Error", 
                                   f"Failed to initialize application: {e}\n\n"
                                   "Please check that:\n"
                                   "1. Camera is connected and not in use\n"
                                   "2. All dependencies are installed\n"
                                   "3. You have necessary permissions")
            sys.exit(1)
    
    def _initialize_components(self):
        """Initialize core application components"""
        try:
            # Initialize components
            self.auth_manager = AuthManager()
            self.performance_monitor = PerformanceMonitor()
            self.sync_manager = SyncManager()
            self.eye_tracker = EyeTrackerUI()
            
            # Initialize enhanced data storage
            from desktop_app.data_storage import SessionDataStorage
            self.data_storage = SessionDataStorage()
            
            # Initialize production eye tracker with error handling
            self.blink_tracker = create_eye_tracker(
                show_preview=False,  # Disable preview for packaged app
                ear_threshold=0.25,
                consec_frames=3,
                detection_confidence=0.7,
                tracking_confidence=0.5
            )
            
            # Set up event callbacks
            self.blink_tracker.add_blink_callback(self._on_blink_detected)
            self.blink_tracker.add_error_callback(self._on_eye_tracker_error)
            
            logger.info("Core components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def _on_blink_detected(self, blink_data: BlinkData):
        """Handle blink detection event with enhanced data storage"""
        try:
            # Get current user
            user_id = self.auth_manager.current_user.id if self.auth_manager.current_user else "anonymous"
            
            # Start session if not already started
            if not self.data_storage.current_session_id:
                self.data_storage.start_session(user_id)
            
            # Save blink event to both SQLite and JSON session format
            success = self.data_storage.save_blink_event(
                blink_count=blink_data.blink_count,
                direction="both",  # Both eyes blinked
                confidence=blink_data.confidence if hasattr(blink_data, 'confidence') else 0.0,
                ear_left=blink_data.ear_left if hasattr(blink_data, 'ear_left') else None,
                ear_right=blink_data.ear_right if hasattr(blink_data, 'ear_right') else None
            )
            
            if success:
                logger.debug(f"Blink event saved: count={blink_data.blink_count}")
            else:
                logger.warning(f"Failed to save blink event: count={blink_data.blink_count}")
            
            # Also buffer to old sync manager for backward compatibility
            try:
                from desktop_app.sync import BlinkEvent
                import uuid
                
                event = BlinkEvent(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    timestamp=blink_data.timestamp,
                    count=blink_data.blink_count,
                    session_id=blink_data.session_id,
                    device_id=blink_data.device_id,
                    open_closed="closed",  # Blink detected
                    direction="both",  # Both eyes
                    confidence=blink_data.confidence if hasattr(blink_data, 'confidence') else 1.0,
                    ear_left=blink_data.ear_left if hasattr(blink_data, 'ear_left') else None,
                    ear_right=blink_data.ear_right if hasattr(blink_data, 'ear_right') else None
                )
                
                self.sync_manager.buffer_event(event)
            except Exception as sync_error:
                logger.warning(f"Old sync manager failed: {sync_error}")
            
        except Exception as e:
            logger.error(f"Error handling blink detection: {e}")
    
    def _on_eye_tracker_error(self, error: Exception):
        """Handle eye tracker errors"""
        logger.error(f"Eye tracker error: {error}")
        
        # Show user-friendly error message
        error_msg = "Eye tracking encountered an issue. "
        
        if "camera" in str(error).lower():
            error_msg += "Please check your camera connection and permissions."
        elif "mediapipe" in str(error).lower():
            error_msg += "There was an issue with face detection. Please ensure good lighting."
        else:
            error_msg += f"Error details: {error}"
        
        # Log for debugging but don't crash the app
        logger.warning(f"Eye tracker error handled gracefully: {error_msg}")
    
    def _show_error_dialog(self, title: str, message: str):
        """Show error dialog to user"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
        except Exception as e:
            # Fallback to console if GUI fails
            print(f"{title}: {message}")
            logger.error(f"Failed to show error dialog: {e}")
    
    def run(self):
        """Start the application with comprehensive error handling"""
        try:
            # Show main window unless headless
            if not getattr(self, '_headless', False):
                self.main_window.show()
            
            # Start background services
            self.performance_monitor.start()
            self.sync_manager.start()
            
            logger.info("Application started successfully")
            
            # Run event loop unless headless (then short no-op loop)
            if getattr(self, '_headless', False):
                logger.info("Running in headless mode; starting and stopping services briefly")
                # Briefly spin to simulate run
                from time import sleep
                sleep(0.5)
                return 0
            return self.app.exec()
            
        except Exception as e:
            logger.error(f"Application failed to start: {e}")
            self._show_error_dialog("Startup Error", f"Application failed to start: {e}")
            return 1
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup application resources"""
        try:
            logger.info("Cleaning up application resources...")
            
            # End current session if active
            if hasattr(self, 'data_storage') and self.data_storage:
                if self.data_storage.current_session_id:
                    json_path = self.data_storage.end_session()
                    if json_path:
                        logger.info(f"Session saved to: {json_path}")
            
            # Stop eye tracking
            if hasattr(self, 'blink_tracker') and self.blink_tracker:
                self.blink_tracker.stop_tracking()
            
            # Stop background services
            if hasattr(self, 'performance_monitor') and self.performance_monitor:
                self.performance_monitor.stop()
            
            if hasattr(self, 'sync_manager') and self.sync_manager:
                self.sync_manager.stop()
            
            logger.info("Application cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main():
    """Main entry point with enhanced error handling"""
    try:
        # Create and run application
        app = WellnessAIApp()
        return app.run()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Critical application error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
