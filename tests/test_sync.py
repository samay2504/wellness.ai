"""
Test suite for synchronization module
Tests local storage, cloud sync, and data management
"""

import unittest
import json
import tempfile
import os
import sqlite3
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from desktop_app.sync import (
    SyncManager, LocalStorage, CloudStorage, 
    BlinkEvent, SyncReport, SyncStatus
)


class TestBlinkEvent(unittest.TestCase):
    """Test BlinkEvent data model"""

    def test_blink_event_creation(self):
        """Test creating a blink event with all fields"""
        event = BlinkEvent(
            id="event123",
            user_id="user123",
            timestamp=time.time(),
            count=5,
            session_id="session123",
            device_id="device123"
        )
        
        self.assertEqual(event.id, "event123")
        self.assertEqual(event.user_id, "user123")
        self.assertEqual(event.count, 5)
        self.assertEqual(event.session_id, "session123")
        self.assertEqual(event.device_id, "device123")

    def test_blink_event_to_dict(self):
        """Test converting blink event to dictionary"""
        timestamp = time.time()
        event = BlinkEvent(
            id="event123",
            user_id="user123",
            timestamp=timestamp,
            count=5,
            session_id="session123",
            device_id="device123"
        )
        
        event_dict = event.to_dict()
        
        self.assertEqual(event_dict["id"], "event123")
        self.assertEqual(event_dict["user_id"], "user123")
        self.assertEqual(event_dict["timestamp"], timestamp)
        self.assertEqual(event_dict["count"], 5)
        self.assertEqual(event_dict["session_id"], "session123")
        self.assertEqual(event_dict["device_id"], "device123")


class TestSyncReport(unittest.TestCase):
    """Test SyncReport data model"""

    def test_sync_report_creation(self):
        """Test creating a sync report"""
        report = SyncReport(
            timestamp=time.time(),
            events_synced=10,
            events_failed=2,
            status=SyncStatus.SUCCESS,
            error_message=None
        )
        
        self.assertEqual(report.events_synced, 10)
        self.assertEqual(report.events_failed, 2)
        self.assertEqual(report.status, SyncStatus.SUCCESS)
        self.assertIsNone(report.error_message)

    def test_sync_report_with_error(self):
        """Test creating a sync report with error"""
        report = SyncReport(
            timestamp=time.time(),
            events_synced=0,
            events_failed=5,
            status=SyncStatus.FAILED,
            error_message="Network error"
        )
        
        self.assertEqual(report.events_synced, 0)
        self.assertEqual(report.events_failed, 5)
        self.assertEqual(report.status, SyncStatus.FAILED)
        self.assertEqual(report.error_message, "Network error")


class TestLocalStorage(unittest.TestCase):
    """Test local storage functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.json_path = os.path.join(self.temp_dir, "test.json")
        
        self.local_storage = LocalStorage(
            db_path=self.db_path,
            json_path=self.json_path
        )

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_init(self):
        """Test LocalStorage initialization"""
        self.assertEqual(self.local_storage.db_path, self.db_path)
        self.assertEqual(self.local_storage.json_path, self.json_path)
        self.assertIsNotNone(self.local_storage.lock)

    def test_create_tables(self):
        """Test database table creation"""
        self.local_storage._create_tables()
        
        # Verify tables exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        self.assertIn("blink_events", tables)
        self.assertIn("sync_history", tables)
        
        conn.close()

    def test_store_blink_event(self):
        """Test storing a blink event"""
        event = BlinkEvent(
            id="event123",
            user_id="user123",
            timestamp=time.time(),
            count=5,
            session_id="session123",
            device_id="device123"
        )
        
        self.local_storage.store_blink_event(event)
        
        # Verify event was stored in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM blink_events WHERE id = ?", ("event123",))
        row = cursor.fetchone()
        
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "event123")  # id
        self.assertEqual(row[1], "user123")   # user_id
        self.assertEqual(row[3], 5)           # count
        
        conn.close()

    def test_get_unsynced_events(self):
        """Test retrieving unsynced events"""
        # Create and store events
        event1 = BlinkEvent(
            id="event1",
            user_id="user123",
            timestamp=time.time(),
            count=5,
            session_id="session123",
            device_id="device123"
        )
        
        event2 = BlinkEvent(
            id="event2",
            user_id="user123",
            timestamp=time.time(),
            count=3,
            session_id="session123",
            device_id="device123"
        )
        
        self.local_storage.store_blink_event(event1)
        self.local_storage.store_blink_event(event2)
        
        # Get unsynced events
        events = self.local_storage.get_unsynced_events()
        
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].id, "event1")
        self.assertEqual(events[1].id, "event2")

    def test_mark_events_synced(self):
        """Test marking events as synced"""
        # Create and store event
        event = BlinkEvent(
            id="event123",
            user_id="user123",
            timestamp=time.time(),
            count=5,
            session_id="session123",
            device_id="device123"
        )
        
        self.local_storage.store_blink_event(event)
        
        # Mark as synced
        self.local_storage.mark_events_synced(["event123"])
        
        # Verify event is marked as synced
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT synced FROM blink_events WHERE id = ?", ("event123",))
        synced = cursor.fetchone()[0]
        
        self.assertEqual(synced, 1)
        
        conn.close()

    def test_backup_to_json(self):
        """Test backing up events to JSON"""
        # Create and store event
        event = BlinkEvent(
            id="event123",
            user_id="user123",
            timestamp=time.time(),
            count=5,
            session_id="session123",
            device_id="device123"
        )
        
        self.local_storage.store_blink_event(event)
        
        # Create backup
        self.local_storage.backup_to_json()
        
        # Verify JSON file exists and contains data
        self.assertTrue(os.path.exists(self.json_path))
        
        with open(self.json_path, 'r') as f:
            data = json.load(f)
        
        self.assertIn("events", data)
        self.assertEqual(len(data["events"]), 1)
        self.assertEqual(data["events"][0]["id"], "event123")


class TestCloudStorage(unittest.TestCase):
    """Test cloud storage functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.cloud_storage = CloudStorage(
            bucket_name="test-bucket",
            region="us-east-1"
        )

    @patch('boto3.client')
    def test_init_s3_client_success(self, mock_boto3_client):
        """Test successful S3 client initialization"""
        mock_s3_client = Mock()
        mock_boto3_client.return_value = mock_s3_client
        
        cloud_storage = CloudStorage()
        
        self.assertEqual(cloud_storage.s3_client, mock_s3_client)
        mock_boto3_client.assert_called_once_with('s3', region_name='us-east-1')

    @patch('boto3.client')
    def test_init_s3_client_failure(self, mock_boto3_client):
        """Test S3 client initialization failure"""
        mock_boto3_client.side_effect = NoCredentialsError()
        
        cloud_storage = CloudStorage()
        
        self.assertIsNone(cloud_storage.s3_client)

    @patch('boto3.client')
    def test_upload_blink_events_success(self, mock_boto3_client):
        """Test successful upload of blink events"""
        mock_s3_client = Mock()
        mock_boto3_client.return_value = mock_s3_client
        
        events = [
            BlinkEvent(
                id="event1",
                user_id="user123",
                timestamp=time.time(),
                count=5,
                session_id="session123",
                device_id="device123"
            ),
            BlinkEvent(
                id="event2",
                user_id="user123",
                timestamp=time.time(),
                count=3,
                session_id="session123",
                device_id="device123"
            )
        ]
        
        self.cloud_storage.s3_client = mock_s3_client
        
        result = self.cloud_storage.upload_blink_events("user123", events)
        
        self.assertTrue(result)
        mock_s3_client.put_object.assert_called_once()

    @patch('boto3.client')
    def test_upload_blink_events_failure(self, mock_boto3_client):
        """Test upload failure"""
        mock_s3_client = Mock()
        mock_s3_client.put_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket does not exist'}},
            'PutObject'
        )
        mock_boto3_client.return_value = mock_s3_client
        
        events = [
            BlinkEvent(
                id="event1",
                user_id="user123",
                timestamp=time.time(),
                count=5,
                session_id="session123",
                device_id="device123"
            )
        ]
        
        self.cloud_storage.s3_client = mock_s3_client
        
        result = self.cloud_storage.upload_blink_events("user123", events)
        
        self.assertFalse(result)

    @patch('boto3.client')
    def test_upload_sync_report_success(self, mock_boto3_client):
        """Test successful upload of sync report"""
        mock_s3_client = Mock()
        mock_boto3_client.return_value = mock_s3_client
        
        report = SyncReport(
            timestamp=time.time(),
            events_synced=10,
            events_failed=0,
            status=SyncStatus.SUCCESS,
            error_message=None
        )
        
        self.cloud_storage.s3_client = mock_s3_client
        
        result = self.cloud_storage.upload_sync_report("user123", report)
        
        self.assertTrue(result)
        mock_s3_client.put_object.assert_called_once()

    @patch('boto3.client')
    def test_delete_user_data_success(self, mock_boto3_client):
        """Test successful deletion of user data"""
        mock_s3_client = Mock()
        mock_s3_client.list_objects_v2.return_value = {
            'Contents': [
                {'Key': 'user123/events/event1.json'},
                {'Key': 'user123/events/event2.json'},
                {'Key': 'user123/reports/report1.json'}
            ]
        }
        mock_boto3_client.return_value = mock_s3_client
        
        self.cloud_storage.s3_client = mock_s3_client
        
        result = self.cloud_storage.delete_user_data("user123")
        
        self.assertTrue(result)
        # Verify delete_objects was called for each file
        self.assertEqual(mock_s3_client.delete_objects.call_count, 1)

# --- GCS Migration Supplemental Tests (appended) ---
class TestGCSFallback(unittest.TestCase):
    """Validate fallback logic when cloud upload fails (simulated)"""
    def test_local_fallback_on_failure(self):
        # Simulate absence of cloud by forcing exception path using CloudStorage with no client
        storage = CloudStorage(bucket_name="dummy", region="us-east-1")
        storage.s3_client = None  # Force unavailable
        events = []  # No events; expect graceful False return
        self.assertFalse(storage.upload_blink_events("user1", events))



class TestSyncManager(unittest.TestCase):
    """Test sync manager functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.json_path = os.path.join(self.temp_dir, "test.json")
        
        self.sync_manager = SyncManager(
            db_path=self.db_path,
            json_path=self.json_path,
            bucket_name="test-bucket"
        )

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_init(self):
        """Test SyncManager initialization"""
        self.assertIsNotNone(self.sync_manager.local_storage)
        self.assertIsNotNone(self.sync_manager.cloud_storage)
        self.assertIsNotNone(self.sync_manager.lock)
        self.assertFalse(self.sync_manager._running)

    @patch.object(SyncManager, '_sync_events')
    def test_start_sync(self, mock_sync_events):
        """Test starting sync process"""
        self.sync_manager.start()
        
        self.assertTrue(self.sync_manager._running)
        self.assertIsNotNone(self.sync_manager.sync_thread)
        self.assertTrue(self.sync_manager.sync_thread.is_alive())

    def test_stop_sync(self):
        """Test stopping sync process"""
        self.sync_manager._running = True
        self.sync_manager.sync_thread = Mock()
        
        self.sync_manager.stop()
        
        self.assertFalse(self.sync_manager._running)
        self.sync_manager.sync_thread.join.assert_called_once()

    @patch.object(SyncManager, 'cloud_storage')
    @patch.object(SyncManager, 'local_storage')
    def test_sync_events_success(self, mock_local_storage, mock_cloud_storage):
        """Test successful event synchronization"""
        # Mock unsynced events
        events = [
            BlinkEvent(
                id="event1",
                user_id="user123",
                timestamp=time.time(),
                count=5,
                session_id="session123",
                device_id="device123"
            )
        ]
        
        mock_local_storage.get_unsynced_events.return_value = events
        mock_cloud_storage.upload_blink_events.return_value = True
        
        # Mock current user
        with patch.object(self.sync_manager, '_get_current_user_id', return_value="user123"):
            self.sync_manager._sync_events()
        
        # Verify events were uploaded and marked as synced
        mock_cloud_storage.upload_blink_events.assert_called_once_with("user123", events)
        mock_local_storage.mark_events_synced.assert_called_once_with(["event1"])

    @patch.object(SyncManager, 'cloud_storage')
    @patch.object(SyncManager, 'local_storage')
    def test_sync_events_failure(self, mock_local_storage, mock_cloud_storage):
        """Test event synchronization failure"""
        # Mock unsynced events
        events = [
            BlinkEvent(
                id="event1",
                user_id="user123",
                timestamp=time.time(),
                count=5,
                session_id="session123",
                device_id="device123"
            )
        ]
        
        mock_local_storage.get_unsynced_events.return_value = events
        mock_cloud_storage.upload_blink_events.return_value = False
        
        # Mock current user
        with patch.object(self.sync_manager, '_get_current_user_id', return_value="user123"):
            self.sync_manager._sync_events()
        
        # Verify events were not marked as synced
        mock_cloud_storage.upload_blink_events.assert_called_once_with("user123", events)
        mock_local_storage.mark_events_synced.assert_not_called()

    @patch.object(SyncManager, 'cloud_storage')
    @patch.object(SyncManager, 'local_storage')
    def test_sync_events_no_user(self, mock_local_storage, mock_cloud_storage):
        """Test sync when no user is authenticated"""
        # Mock unsynced events
        events = [
            BlinkEvent(
                id="event1",
                user_id="user123",
                timestamp=time.time(),
                count=5,
                session_id="session123",
                device_id="device123"
            )
        ]
        
        mock_local_storage.get_unsynced_events.return_value = events
        
        # Mock no current user
        with patch.object(self.sync_manager, '_get_current_user_id', return_value=None):
            self.sync_manager._sync_events()
        
        # Verify no upload was attempted
        mock_cloud_storage.upload_blink_events.assert_not_called()

    def test_get_sync_status(self):
        """Test getting sync status"""
        # Mock local storage
        with patch.object(self.sync_manager.local_storage, 'get_unsynced_events') as mock_get_events:
            mock_get_events.return_value = []
            
            status = self.sync_manager.get_sync_status()
            
            self.assertEqual(status.events_pending, 0)
            self.assertEqual(status.last_sync, None)
            self.assertEqual(status.status, "idle")

    def test_get_sync_status_with_pending_events(self):
        """Test getting sync status with pending events"""
        # Mock local storage
        with patch.object(self.sync_manager.local_storage, 'get_unsynced_events') as mock_get_events:
            mock_get_events.return_value = [Mock(), Mock()]  # 2 pending events
            
            status = self.sync_manager.get_sync_status()
            
            self.assertEqual(status.events_pending, 2)
            self.assertEqual(status.status, "pending")


if __name__ == '__main__':
    unittest.main() 