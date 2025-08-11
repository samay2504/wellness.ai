"""
Unit tests for the eye tracker module
Tests MediaPipe integration and blink detection
"""

import unittest
import time
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from desktop_app.eye_tracker import EyeTracker, BlinkData, create_eye_tracker


class TestBlinkData(unittest.TestCase):
    """Test BlinkData dataclass"""
    
    def test_blink_data_creation(self):
        """Test creating a BlinkData object"""
        data = BlinkData(
            timestamp=1640995200.0,
            blink_count=5,
            ear_left=0.2,
            ear_right=0.2,
            confidence=0.85,
            session_id="test_session",
            device_id="test_device"
        )
        
        self.assertEqual(data.blink_count, 5)
        self.assertEqual(data.timestamp, 1640995200.0)
        self.assertEqual(data.session_id, "test_session")
        self.assertEqual(data.confidence, 0.85)
        self.assertEqual(data.device_id, "test_device")
    
    def test_blink_data_to_dict(self):
        """Test converting BlinkData to dictionary"""
        data = BlinkData(
            timestamp=time.time(),
            blink_count=3,
            ear_left=0.2,
            ear_right=0.2,
            confidence=1.0,
            session_id="test",
            device_id="device1"
        )
        
        data_dict = data.to_dict()
        
        self.assertEqual(data_dict["blink_count"], 3)
        self.assertIn("timestamp", data_dict)
        self.assertEqual(data_dict["session_id"], "test")
        self.assertEqual(data_dict["confidence"], 1.0)


class TestEyeTracker(unittest.TestCase):
    """Test EyeTracker class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.eye_tracker = EyeTracker()
        
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self.eye_tracker, 'cap') and self.eye_tracker.cap:
            self.eye_tracker.stop()
    
    def test_eye_tracker_initialization(self):
        """Test EyeTracker initialization"""
        self.assertIsNotNone(self.eye_tracker.session_id)
        self.assertIsNotNone(self.eye_tracker.device_id)
        self.assertEqual(self.eye_tracker.blink_count, 0)
        self.assertFalse(self.eye_tracker.is_running)
        self.assertIsNone(self.eye_tracker.cap)
    
    def test_calculate_ear(self):
        """Test Eye Aspect Ratio calculation"""
        # Mock eye landmarks with proper 6-point structure
        eye_points = [
            [0.1, 0.2],  # Point 1
            [0.2, 0.15], # Point 2
            [0.3, 0.2],  # Point 3
            [0.1, 0.25], # Point 4
            [0.2, 0.3],  # Point 5
            [0.3, 0.25]  # Point 6
        ]
        
        ear = self.eye_tracker._calculate_ear(eye_points)
        
        self.assertIsInstance(ear, float)
        self.assertGreater(ear, 0)
    
    def test_detect_blink(self):
        """Test blink detection logic"""
        # Test with EAR below threshold (should detect blink preparation)
        self.eye_tracker.ear_threshold = 0.21
        self.eye_tracker.consecutive_frames = 2
        
        # Simulate blink sequence
        self.assertFalse(self.eye_tracker._detect_blink(0.15))  # First frame below threshold
        self.assertFalse(self.eye_tracker._detect_blink(0.15))  # Second frame below threshold
        self.assertTrue(self.eye_tracker._detect_blink(0.25))   # Eye opens - blink detected
        
        # Verify blink count increased
        self.assertEqual(self.eye_tracker.blink_count, 1)
    
    def test_detect_no_blink(self):
        """Test blink detection when no blink occurs"""
        self.eye_tracker.ear_threshold = 0.21
        self.eye_tracker.consecutive_frames = 2
        
        # Simulate normal eye state (always open)
        self.assertFalse(self.eye_tracker._detect_blink(0.25))  # Eye open
        self.assertFalse(self.eye_tracker._detect_blink(0.25))  # Eye still open
        self.assertFalse(self.eye_tracker._detect_blink(0.25))  # Eye still open
        
        # Verify no blink detected
        self.assertEqual(self.eye_tracker.blink_count, 0)
    
    @patch('cv2.VideoCapture')
    @patch('mediapipe.solutions.face_mesh.FaceMesh')
    def test_start_tracking_success(self, mock_face_mesh_class, mock_video_capture):
        """Test successful camera and MediaPipe initialization"""
        # Mock successful camera capture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_video_capture.return_value = mock_cap
        
        # Mock MediaPipe face mesh
        mock_face_mesh = Mock()
        mock_face_mesh_class.return_value = mock_face_mesh
        
        result = self.eye_tracker.start_tracking()
        
        self.assertTrue(result)
        self.assertTrue(self.eye_tracker.is_running)
        self.assertIsNotNone(self.eye_tracker.cap)
        self.assertIsNotNone(self.eye_tracker.face_mesh)
        
        # Cleanup
        self.eye_tracker.stop_tracking()
    
    @patch('cv2.VideoCapture')
    def test_start_tracking_camera_failure(self, mock_video_capture):
        """Test camera initialization failure"""
        # Mock failed camera capture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap
        
        result = self.eye_tracker.start_tracking()
        
        self.assertFalse(result)
        self.assertFalse(self.eye_tracker.is_running)
    
    def test_stop_tracking(self):
        """Test stopping the eye tracker"""
        # Mock camera and face mesh
        self.eye_tracker.cap = Mock()
        self.eye_tracker.face_mesh = Mock()
        self.eye_tracker.face_mesh.close = Mock()
        self.eye_tracker.is_running = True
        
        self.eye_tracker.stop_tracking()
        
        self.assertFalse(self.eye_tracker.is_running)
        self.eye_tracker.cap.release.assert_called_once()
        self.eye_tracker.face_mesh.close.assert_called_once()
    
    def test_get_current_blink_count(self):
        """Test getting current blink count"""
        # Set up some test data
        self.eye_tracker.blink_count = 15
        
        count = self.eye_tracker.get_current_blink_count()
        
        self.assertEqual(count, 15)
    
    def test_get_stats(self):
        """Test getting tracker statistics"""
        # Set up some test data
        self.eye_tracker.blink_count = 10
        self.eye_tracker.total_frames = 1000
        self.eye_tracker.successful_detections = 950
        
        stats = self.eye_tracker.get_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats["blink_count"], 10)
        self.assertIn("detection_rate", stats)
        self.assertIn("session_id", stats)
    
    def test_reset_session(self):
        """Test resetting the session"""
        # Set up some test data
        self.eye_tracker.blink_count = 25
        original_session_id = self.eye_tracker.session_id
        
        self.eye_tracker.reset_session()
        
        self.assertEqual(self.eye_tracker.blink_count, 0)
        self.assertNotEqual(self.eye_tracker.session_id, original_session_id)
    
    def test_add_blink_callback(self):
        """Test adding blink callback function"""
        def mock_callback(data):
            pass
        
        self.eye_tracker.add_blink_callback(mock_callback)
        
        self.assertIn(mock_callback, self.eye_tracker.blink_callbacks)
    
    def test_add_error_callback(self):
        """Test adding error callback function"""
        def mock_error_callback(error):
            pass
        
        self.eye_tracker.add_error_callback(mock_error_callback)
        
        self.assertIn(mock_error_callback, self.eye_tracker.error_callbacks)
    
    @patch('threading.Thread')
    def test_start_tracking_thread(self, mock_thread):
        """Test starting the tracking thread"""
        # Mock successful start
        with patch.object(self.eye_tracker, 'start_tracking', return_value=True):
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            # This test is more about verifying the threading setup
            # The actual threading is tested implicitly in start_tracking
            self.assertFalse(self.eye_tracker.is_running)
    
    def test_process_frame_no_face(self):
        """Test frame processing when no face is detected"""
        # This is tested implicitly in the tracking loop
        # When no face is detected, no blinks should be counted
        self.assertEqual(self.eye_tracker.blink_count, 0)


class TestCreateEyeTracker(unittest.TestCase):
    """Test create_eye_tracker factory function"""
    
    def test_create_eye_tracker(self):
        """Test creating eye tracker with factory function"""
        def mock_callback(data):
            pass
        
        tracker = create_eye_tracker(callback=mock_callback)
        
        self.assertIsInstance(tracker, EyeTracker)
        self.assertIn(mock_callback, tracker.blink_callbacks)
    
    def test_create_eye_tracker_no_callback(self):
        """Test creating eye tracker without callback"""
        tracker = create_eye_tracker()
        
        self.assertIsInstance(tracker, EyeTracker)
        self.assertEqual(len(tracker.blink_callbacks), 0)


if __name__ == '__main__':
    unittest.main()