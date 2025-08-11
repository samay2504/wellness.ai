"""
Integration tests for Wellness at Work
Tests the complete system including desktop app, backend API, and web dashboard
"""

import unittest
import json
import time
import tempfile
import os
import sqlite3
import requests
import subprocess
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from desktop_app.auth import AuthManager
from desktop_app.core.eye_tracker import EyeTracker
from desktop_app.sync import SyncManager
from desktop_app.metrics import PerformanceMonitor


class TestSystemIntegration(unittest.TestCase):
    """Integration tests for the complete system"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_integration.db")
        self.json_path = os.path.join(self.temp_dir, "test_integration.json")
        
        # Test configuration
        self.test_config = {
            'api_url': 'http://localhost:5000',
            'test_user': {
                'email': 'test@example.com',
                'password': 'testpassword123',
                'name': 'Test User'
            }
        }
        
        # Initialize components
        self.auth_manager = AuthManager()
        self.eye_tracker = EyeTracker()
        self.sync_manager = SyncManager(
            db_path=self.db_path,
            json_path=self.json_path
        )
        self.performance_monitor = PerformanceMonitor()

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
        # Stop all components
        self.eye_tracker.stop()
        self.performance_monitor.stop()
        self.sync_manager.stop()

    def test_user_registration_and_login_flow(self):
        """Test complete user registration and login flow"""
        # Test user registration
        user_data = {
            'email': self.test_config['test_user']['email'],
            'password': self.test_config['test_user']['password'],
            'name': self.test_config['test_user']['name']
        }
        
        # Mock API registration
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                'message': 'User created successfully',
                'token': 'test-jwt-token',
                'user': {
                    'id': 'test123',
                    'email': user_data['email'],
                    'name': user_data['name']
                }
            }
            mock_post.return_value = mock_response
            
            # Test registration
            result = self.auth_manager.register_user(user_data)
            self.assertIsNotNone(result)
            self.assertEqual(result['email'], user_data['email'])
        
        # Test user login
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'message': 'Login successful',
                'token': 'test-jwt-token',
                'user': {
                    'id': 'test123',
                    'email': user_data['email'],
                    'name': user_data['name']
                }
            }
            mock_post.return_value = mock_response
            
            # Test login
            result = self.auth_manager.login(user_data['email'], user_data['password'])
            self.assertIsNotNone(result)
            self.assertEqual(result['email'], user_data['email'])

    def test_eye_tracking_data_flow(self):
        """Test complete eye tracking data flow from capture to storage"""
        # Start eye tracker
        self.eye_tracker.start(user_id='test123')
        time.sleep(2)  # Allow time for initialization
        
        # Simulate blink detection
        blink_data = {
            'timestamp': time.time(),
            'ear_left': 0.15,
            'ear_right': 0.16,
            'ear_avg': 0.155,
            'is_blink': True,
            'blink_count': 1
        }
        
        # Test blink event creation
        blink_event = self.sync_manager.create_blink_event(
            user_id='test123',
            timestamp=blink_data['timestamp'],
            count=blink_data['blink_count']
        )
        
        self.assertIsNotNone(blink_event)
        self.assertEqual(blink_event.user_id, 'test123')
        self.assertEqual(blink_event.count, 1)
        
        # Test local storage
        self.sync_manager.local_storage.store_blink_event(blink_event)
        
        # Verify event is stored locally
        stored_events = self.sync_manager.local_storage.get_unsynced_events()
        self.assertEqual(len(stored_events), 1)
        self.assertEqual(stored_events[0].user_id, 'test123')

    def test_data_synchronization_flow(self):
        """Test data synchronization between local storage and cloud"""
        # Create test blink events
        events = []
        for i in range(5):
            event = self.sync_manager.create_blink_event(
                user_id='test123',
                timestamp=time.time() + i,
                count=i + 1
            )
            events.append(event)
            self.sync_manager.local_storage.store_blink_event(event)
        
        # Verify events are stored locally
        stored_events = self.sync_manager.local_storage.get_unsynced_events()
        self.assertEqual(len(stored_events), 5)
        
        # Mock cloud sync
        with patch.object(self.sync_manager.cloud_storage, 'upload_blink_events') as mock_upload:
            mock_upload.return_value = True
            
            # Test synchronization
            sync_result = self.sync_manager.sync_events()
            self.assertTrue(sync_result)
            
            # Verify events were uploaded
            mock_upload.assert_called_once_with('test123', stored_events)
            
            # Verify events are marked as synced
            synced_events = self.sync_manager.local_storage.get_unsynced_events()
            self.assertEqual(len(synced_events), 0)

    def test_performance_monitoring_integration(self):
        """Test performance monitoring integration"""
        # Start performance monitoring
        self.performance_monitor.start()
        time.sleep(1)  # Allow time for metrics collection
        
        # Get performance metrics
        metrics = self.performance_monitor.get_metrics()
        
        # Verify metrics are collected
        self.assertIsNotNone(metrics)
        self.assertIn('cpu_percent', metrics)
        self.assertIn('memory_mb', metrics)
        self.assertIn('memory_percent', metrics)
        self.assertIn('energy_impact', metrics)
        
        # Verify metric values are reasonable
        self.assertGreaterEqual(metrics['cpu_percent'], 0)
        self.assertLessEqual(metrics['cpu_percent'], 100)
        self.assertGreaterEqual(metrics['memory_percent'], 0)
        self.assertLessEqual(metrics['memory_percent'], 100)

    def test_offline_functionality(self):
        """Test application functionality when offline"""
        # Create events while offline
        events = []
        for i in range(3):
            event = self.sync_manager.create_blink_event(
                user_id='test123',
                timestamp=time.time() + i,
                count=i + 1
            )
            events.append(event)
            self.sync_manager.local_storage.store_blink_event(event)
        
        # Verify events are stored locally
        stored_events = self.sync_manager.local_storage.get_unsynced_events()
        self.assertEqual(len(stored_events), 3)
        
        # Mock network failure
        with patch.object(self.sync_manager.cloud_storage, 'upload_blink_events') as mock_upload:
            mock_upload.side_effect = Exception("Network error")
            
            # Test sync failure handling
            sync_result = self.sync_manager.sync_events()
            self.assertFalse(sync_result)
            
            # Verify events remain unsynced
            unsynced_events = self.sync_manager.local_storage.get_unsynced_events()
            self.assertEqual(len(unsynced_events), 3)

    def test_gdpr_compliance_features(self):
        """Test GDPR compliance features"""
        # Create test user data
        user_data = {
            'id': 'test123',
            'email': 'test@example.com',
            'name': 'Test User',
            'consent': True
        }
        
        # Test data export
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'user': user_data,
                'events': [
                    {
                        'id': 'event1',
                        'timestamp': time.time(),
                        'count': 1
                    }
                ],
                'export_date': datetime.utcnow().isoformat()
            }
            mock_get.return_value = mock_response
            
            # Test data export
            export_data = self.auth_manager.export_user_data()
            self.assertIsNotNone(export_data)
            self.assertIn('user', export_data)
            self.assertIn('events', export_data)
        
        # Test data deletion
        with patch('requests.delete') as mock_delete:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_delete.return_value = mock_response
            
            # Test account deletion
            result = self.auth_manager.delete_user_account()
            self.assertTrue(result)

    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms"""
        # Test invalid authentication
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {'message': 'Invalid credentials'}
            mock_post.return_value = mock_response
            
            # Test login failure
            result = self.auth_manager.login('invalid@email.com', 'wrongpassword')
            self.assertIsNone(result)
        
        # Test network timeout handling
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
            
            # Test timeout handling
            result = self.auth_manager.login('test@email.com', 'password')
            self.assertIsNone(result)
        
        # Test database corruption recovery
        # Corrupt the database file
        with open(self.db_path, 'w') as f:
            f.write('corrupted data')
        
        # Test recovery
        self.sync_manager.local_storage._create_tables()
        
        # Verify database is functional
        test_event = self.sync_manager.create_blink_event(
            user_id='test123',
            timestamp=time.time(),
            count=1
        )
        self.sync_manager.local_storage.store_blink_event(test_event)
        
        stored_events = self.sync_manager.local_storage.get_unsynced_events()
        self.assertEqual(len(stored_events), 1)

    def test_cross_platform_compatibility(self):
        """Test cross-platform compatibility"""
        # Test platform detection
        import platform
        current_platform = platform.system()
        
        # Test platform-specific features
        if current_platform == 'Windows':
            # Test Windows-specific functionality
            self.assertTrue(hasattr(self.performance_monitor, 'get_windows_metrics'))
        elif current_platform == 'Darwin':  # macOS
            # Test macOS-specific functionality
            self.assertTrue(hasattr(self.performance_monitor, 'get_macos_metrics'))
        elif current_platform == 'Linux':
            # Test Linux-specific functionality
            self.assertTrue(hasattr(self.performance_monitor, 'get_linux_metrics'))
        
        # Test file path handling
        test_path = Path(self.temp_dir) / 'test_file.txt'
        test_path.write_text('test content')
        
        # Verify file operations work across platforms
        self.assertTrue(test_path.exists())
        self.assertEqual(test_path.read_text(), 'test content')

    def test_security_features(self):
        """Test security features and data protection"""
        # Test password hashing
        test_password = 'testpassword123'
        hashed_password = self.auth_manager.hash_password(test_password)
        
        self.assertNotEqual(test_password, hashed_password)
        self.assertTrue(self.auth_manager.verify_password(test_password, hashed_password))
        
        # Test token generation and validation
        test_user = {'id': 'test123', 'email': 'test@example.com'}
        token = self.auth_manager.generate_token(test_user)
        
        self.assertIsNotNone(token)
        decoded_user = self.auth_manager.validate_token(token)
        self.assertEqual(decoded_user['id'], test_user['id'])
        
        # Test data encryption
        test_data = {'sensitive': 'data'}
        encrypted_data = self.auth_manager.encrypt_data(test_data)
        decrypted_data = self.auth_manager.decrypt_data(encrypted_data)
        
        self.assertEqual(test_data, decrypted_data)

    def test_concurrent_operations(self):
        """Test concurrent operations and thread safety"""
        import threading
        import queue
        
        # Create a queue for results
        results = queue.Queue()
        
        def create_events(thread_id):
            """Create events in a separate thread"""
            try:
                for i in range(10):
                    event = self.sync_manager.create_blink_event(
                        user_id=f'user{thread_id}',
                        timestamp=time.time() + i,
                        count=i + 1
                    )
                    self.sync_manager.local_storage.store_blink_event(event)
                results.put(f'thread_{thread_id}_success')
            except Exception as e:
                results.put(f'thread_{thread_id}_error: {str(e)}')
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=create_events, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        thread_results = []
        while not results.empty():
            thread_results.append(results.get())
        
        # Verify all threads completed successfully
        self.assertEqual(len(thread_results), 3)
        for result in thread_results:
            self.assertIn('success', result)
        
        # Verify data integrity
        total_events = 0
        for i in range(3):
            user_events = self.sync_manager.local_storage.get_events_by_user(f'user{i}')
            total_events += len(user_events)
        
        self.assertEqual(total_events, 30)  # 3 threads * 10 events each

    def test_memory_management(self):
        """Test memory management and cleanup"""
        import gc
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create many events
        events = []
        for i in range(1000):
            event = self.sync_manager.create_blink_event(
                user_id='test123',
                timestamp=time.time() + i,
                count=i + 1
            )
            events.append(event)
            self.sync_manager.local_storage.store_blink_event(event)
        
        # Force garbage collection
        gc.collect()
        
        # Get memory usage after creating events
        memory_after_events = process.memory_info().rss
        
        # Clear events
        events.clear()
        gc.collect()
        
        # Get memory usage after clearing
        memory_after_clear = process.memory_info().rss
        
        # Verify memory is properly managed
        # Memory should not grow excessively
        memory_growth = memory_after_events - initial_memory
        self.assertLess(memory_growth, 50 * 1024 * 1024)  # Less than 50MB growth
        
        # Memory should be reclaimed after clearing
        memory_reclaimed = memory_after_events - memory_after_clear
        self.assertGreater(memory_reclaimed, 0)

    def test_performance_benchmarks(self):
        """Test performance benchmarks and optimization"""
        import time
        
        # Benchmark event creation
        start_time = time.time()
        events = []
        for i in range(1000):
            event = self.sync_manager.create_blink_event(
                user_id='test123',
                timestamp=time.time() + i,
                count=i + 1
            )
            events.append(event)
        event_creation_time = time.time() - start_time
        
        # Benchmark database operations
        start_time = time.time()
        for event in events:
            self.sync_manager.local_storage.store_blink_event(event)
        db_operation_time = time.time() - start_time
        
        # Benchmark data retrieval
        start_time = time.time()
        stored_events = self.sync_manager.local_storage.get_unsynced_events()
        retrieval_time = time.time() - start_time
        
        # Performance assertions
        self.assertLess(event_creation_time, 1.0)  # Less than 1 second for 1000 events
        self.assertLess(db_operation_time, 2.0)    # Less than 2 seconds for DB operations
        self.assertLess(retrieval_time, 0.5)       # Less than 0.5 seconds for retrieval
        
        # Verify data integrity
        self.assertEqual(len(stored_events), 1000)

    def test_api_endpoint_integration(self):
        """Test API endpoint integration"""
        # Test health check endpoint
        try:
            response = requests.get(f"{self.test_config['api_url']}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                self.assertEqual(health_data['status'], 'healthy')
        except requests.exceptions.RequestException:
            # API server not running, skip test
            self.skipTest("API server not available")
        
        # Test authentication endpoints
        auth_data = {
            'email': self.test_config['test_user']['email'],
            'password': self.test_config['test_user']['password']
        }
        
        try:
            # Test login endpoint
            response = requests.post(
                f"{self.test_config['api_url']}/auth/login",
                json=auth_data,
                timeout=5
            )
            
            if response.status_code == 200:
                login_data = response.json()
                self.assertIn('token', login_data)
                self.assertIn('user', login_data)
                
                # Test protected endpoint
                headers = {'Authorization': f"Bearer {login_data['token']}"}
                response = requests.get(
                    f"{self.test_config['api_url']}/api/user/profile",
                    headers=headers,
                    timeout=5
                )
                
                if response.status_code == 200:
                    profile_data = response.json()
                    self.assertEqual(profile_data['email'], auth_data['email'])
        except requests.exceptions.RequestException:
            # API server not running, skip test
            self.skipTest("API server not available")


if __name__ == '__main__':
    unittest.main() 