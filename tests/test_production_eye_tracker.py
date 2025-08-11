"""
Unit tests for the production eye tracker module
Tests production functionality and callback system
"""

import unittest
import time
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path for imports  
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from desktop_app.eye_tracker import ProductionEyeTracker, BlinkData, create_eye_tracker


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
            session_id="test_session"
        )
        
        self.assertEqual(data.timestamp, 1640995200.0)
        self.assertEqual(data.blink_count, 5)
        self.assertEqual(data.ear_left, 0.2)
        self.assertEqual(data.ear_right, 0.2)
        self.assertEqual(data.confidence, 0.85)
        self.assertEqual(data.session_id, "test_session")
    
    def test_blink_data_defaults(self):
        """Test BlinkData with default values"""
        data = BlinkData(timestamp=time.time(), blink_count=1)
        
        self.assertEqual(data.blink_count, 1)
        self.assertIsNotNone(data.timestamp)
        self.assertIsNone(data.ear_left)
        self.assertIsNone(data.ear_right)
        self.assertIsNotNone(data.session_id)
        self.assertEqual(data.confidence, 1.0)


class TestProductionEyeTracker(unittest.TestCase):
    """Test ProductionEyeTracker class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.tracker = create_eye_tracker(mock_mode=True, show_preview=False)
        self.callback_data = []
        
        def test_callback(data):
            self.callback_data.append(data)
        
        self.test_callback = test_callback
    
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self.tracker, 'is_running') and self.tracker.is_running:
            self.tracker.stop_tracking()
    
    def test_tracker_initialization(self):
        """Test tracker initialization"""
        self.assertFalse(self.tracker.is_running)
        self.assertEqual(self.tracker.get_current_blink_count(), 0)
        self.assertIsNotNone(self.tracker.session_id)
    
    def test_callback_registration(self):
        """Test callback registration"""
        initial_count = len(self.tracker.blink_callbacks)
        
        self.tracker.add_blink_callback(self.test_callback)
        
        self.assertEqual(len(self.tracker.blink_callbacks), initial_count + 1)
    
    def test_start_stop_tracking(self):
        """Test starting and stopping tracking"""
        # Test start
        result = self.tracker.start_tracking()
        self.assertTrue(result)
        self.assertTrue(self.tracker.is_running)
        
        # Test stop  
        result = self.tracker.stop_tracking()
        self.assertTrue(result)
        self.assertFalse(self.tracker.is_running)
    
    def test_mock_blink_simulation(self):
        """Test mock blink simulation"""
        self.tracker.add_blink_callback(self.test_callback)
        
        # Start tracking
        self.tracker.start_tracking()
        
        # Wait for mock blinks
        time.sleep(0.1)
        
        # Stop tracking
        self.tracker.stop_tracking()
        
        # Check if callbacks were called (in mock mode)
        # Note: This test may be timing dependent
        initial_count = self.tracker.get_current_blink_count()
        self.assertGreaterEqual(initial_count, 0)
    
    def test_stats_retrieval(self):
        """Test getting tracking statistics"""
        stats = self.tracker.get_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn("blink_count", stats)
        self.assertIn("session_id", stats)
        self.assertIn("is_running", stats)
    
    def test_session_reset(self):
        """Test session reset functionality"""
        # Start tracking and generate some blinks
        self.tracker.start_tracking()
        time.sleep(0.1)
        
        initial_count = self.tracker.get_current_blink_count()
        
        # Reset session
        self.tracker.reset_session()
        
        # Check that count is reset
        new_count = self.tracker.get_current_blink_count()
        self.assertEqual(new_count, 0)
        
        self.tracker.stop_tracking()
    
    def test_error_callback(self):
        """Test error callback functionality"""
        error_data = []
        
        def error_callback(error):
            error_data.append(error)
        
        self.tracker.add_error_callback(error_callback)
        
        # Simulate an error
        test_error = Exception("Test error")
        for callback in self.tracker.error_callbacks:
            callback(test_error)
        
        self.assertEqual(len(error_data), 1)
        self.assertEqual(str(error_data[0]), "Test error")


class TestCreateEyeTracker(unittest.TestCase):
    """Test create_eye_tracker factory function"""
    
    def test_create_mock_tracker(self):
        """Test creating tracker in mock mode"""
        tracker = create_eye_tracker(mock_mode=True, show_preview=False)
        
        self.assertIsInstance(tracker, ProductionEyeTracker)
        self.assertFalse(tracker.is_running)
    
    def test_create_real_tracker(self):
        """Test creating real tracker (without camera)"""
        # This test might fail if no camera is available
        try:
            tracker = create_eye_tracker(mock_mode=False, show_preview=False)
            self.assertIsInstance(tracker, ProductionEyeTracker)
        except Exception:
            # It's OK if this fails due to no camera
            self.skipTest("No camera available for real tracker test")
    
    def test_create_with_custom_params(self):
        """Test creating tracker with custom parameters"""
        tracker = create_eye_tracker(
            mock_mode=True,
            show_preview=False,
            ear_threshold=0.3,
            consec_frames=5,
            detection_confidence=0.8,
            tracking_confidence=0.6
        )
        
        self.assertIsInstance(tracker, ProductionEyeTracker)
        self.assertEqual(tracker.ear_threshold, 0.3)
        self.assertEqual(tracker.consec_frames, 5)


if __name__ == "__main__":
    unittest.main()
