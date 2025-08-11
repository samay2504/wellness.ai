"""
Integration script to use the improved eye tracker in the desktop application
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(), 
                              logging.FileHandler('eye_tracker_integration.log')])

logger = logging.getLogger(__name__)

# Add local storage directories
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
(data_dir / "eye_tracking").mkdir(exist_ok=True)

# Import improved eye tracker
try:
    # First try the improved version
    from src.desktop_app.core.improved_eye_tracker import EyeTracker, BlinkEvent
    logger.info("Using improved eye tracker with local storage")
except ImportError:
    try:
        # Fall back to the original eye tracker
        from src.desktop_app.core.eye_tracker import EyeTracker, BlinkEvent
        logger.info("Using original eye tracker")
    except ImportError:
        logger.error("Could not import eye tracker module")
        EyeTracker = None
        BlinkEvent = None

# Import sync module with fallback
try:
    from src.desktop_app.sync import CloudSync
    has_cloud_sync = True
    logger.info("Cloud sync module available")
except ImportError:
    has_cloud_sync = False
    logger.warning("Cloud sync module not available, using local storage only")


class EyeTrackerManager:
    """Manager class that handles eye tracker operations with fallbacks"""
    
    def __init__(self, use_cloud=True):
        self.eye_tracker = None
        self.sync_enabled = use_cloud and has_cloud_sync
        self.sync_client = CloudSync() if self.sync_enabled else None
        
        # Status flags
        self.is_initialized = False
        self.sync_errors = 0
        
        # Try to initialize
        self._initialize()
        
    def _initialize(self):
        """Initialize the eye tracker"""
        if EyeTracker is None:
            logger.error("Eye tracker class not available")
            return False
            
        try:
            self.eye_tracker = EyeTracker(use_local_storage=True)
            self.is_initialized = True
            logger.info("Eye tracker initialized successfully")
            return True
        except Exception as e:
            logger.exception("Failed to initialize eye tracker")
            self.is_initialized = False
            return False
            
    def start_tracking(self):
        """Start eye tracking with proper error handling"""
        if not self.is_initialized:
            if not self._initialize():
                return False
                
        try:
            self.eye_tracker.start()
            logger.info("Eye tracking started")
            return True
        except Exception as e:
            logger.exception("Failed to start eye tracking")
            return False
            
    def stop_tracking(self):
        """Stop eye tracking"""
        if self.eye_tracker and self.eye_tracker.is_running():
            try:
                self.eye_tracker.stop()
                logger.info("Eye tracking stopped")
                
                # Try to sync data if enabled
                if self.sync_enabled:
                    self._sync_data()
                    
                return True
            except Exception as e:
                logger.exception("Error stopping eye tracker")
                return False
        return True
        
    def get_tracking_status(self):
        """Get current tracking status"""
        if not self.eye_tracker:
            return {
                "initialized": False,
                "running": False,
                "blink_count": 0,
                "sync_available": self.sync_enabled,
                "sync_errors": self.sync_errors
            }
            
        try:
            status = self.eye_tracker.get_current_stats()
            status.update({
                "initialized": self.is_initialized,
                "sync_available": self.sync_enabled,
                "sync_errors": self.sync_errors
            })
            return status
        except Exception as e:
            logger.exception("Error getting tracking status")
            return {
                "initialized": self.is_initialized,
                "running": False,
                "error": str(e),
                "sync_available": self.sync_enabled,
                "sync_errors": self.sync_errors
            }
            
    def _sync_data(self):
        """Sync data to cloud if available"""
        if not self.sync_enabled or not self.sync_client:
            return False
            
        try:
            # Get blink events
            events = self.eye_tracker.export_data()
            
            # Only sync if we have events
            if not events:
                return True
                
            # Convert events to dict
            event_dicts = [e.to_dict() for e in events]
            
            # Send to cloud
            result = self.sync_client.upload_blink_data(event_dicts)
            
            if result:
                logger.info(f"Successfully synced {len(events)} blink events")
                return True
            else:
                self.sync_errors += 1
                logger.warning("Failed to sync blink data")
                return False
                
        except Exception as e:
            self.sync_errors += 1
            logger.exception("Error syncing data")
            return False
            
    def get_local_sessions(self):
        """Get list of locally stored sessions"""
        try:
            if hasattr(self.eye_tracker, 'get_local_sessions'):
                return self.eye_tracker.get_local_sessions()
            else:
                # Fallback to manual file search
                sessions_dir = Path("data") / "eye_tracking"
                sessions = []
                
                if sessions_dir.exists():
                    for file_path in sessions_dir.glob("blinks_*.json"):
                        sessions.append({
                            "session_id": file_path.stem.replace("blinks_", ""),
                            "file_path": str(file_path),
                            "file_size": file_path.stat().st_size
                        })
                        
                return sessions
        except Exception as e:
            logger.exception("Error getting local sessions")
            return []
            
    def force_sync(self):
        """Force synchronization of all local data"""
        if not self.sync_enabled:
            logger.warning("Sync not enabled")
            return False
            
        try:
            sessions = self.get_local_sessions()
            synced = 0
            
            for session in sessions:
                try:
                    file_path = session["file_path"]
                    result = self.sync_client.upload_session_file(file_path)
                    if result:
                        synced += 1
                except Exception:
                    logger.exception(f"Error syncing session {session['session_id']}")
                    
            logger.info(f"Synced {synced} of {len(sessions)} sessions")
            return synced > 0
            
        except Exception as e:
            logger.exception("Error during force sync")
            return False


# Example usage
if __name__ == "__main__":
    # Create manager
    manager = EyeTrackerManager(use_cloud=True)
    
    # Check status
    print("Status:", manager.get_tracking_status())
    
    # Start tracking for 10 seconds
    if manager.start_tracking():
        import time
        print("Tracking started, will run for 10 seconds...")
        
        for i in range(10):
            time.sleep(1)
            status = manager.get_tracking_status()
            print(f"Blinks: {status.get('blink_count', 0)}")
        
        manager.stop_tracking()
        print("Tracking stopped")
    
    # Check local sessions
    sessions = manager.get_local_sessions()
    print(f"Found {len(sessions)} local sessions")
    
    # Try to sync
    if has_cloud_sync:
        manager.force_sync()
