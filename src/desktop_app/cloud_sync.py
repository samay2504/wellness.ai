"""
Cloud Sync Service for WellnessAI
Handles offline/online data synchronization
"""

import os
import json
import time
import logging
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

class CloudSyncService(QThread):
    """Enhanced cloud synchronization service"""
    
    # Signals
    sync_started = pyqtSignal()
    sync_progress = pyqtSignal(int, int)  # current, total
    sync_completed = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, user_data: Dict):
        super().__init__()
        self.user_data = user_data
        self.api_base_url = os.getenv('API_BASE_URL', 'http://127.0.0.1:5001')
        self.sync_queue = []
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
    def queue_session_data(self, session_data: Dict):
        """Add session data to sync queue"""
        try:
            # Add timestamp and user info
            sync_item = {
                'type': 'blink_session',
                'data': session_data,
                'user_id': self.user_data.get('id'),
                'queued_at': datetime.now().isoformat(),
                'retry_count': 0
            }
            
            self.sync_queue.append(sync_item)
            logger.info(f"Added session to sync queue: {session_data.get('session_id')}")
            
            # Save queue to disk for persistence
            self._save_sync_queue()
            
        except Exception as e:
            logger.error(f"Failed to queue session data: {e}")
    
    def _save_sync_queue(self):
        """Save sync queue to disk for offline persistence"""
        try:
            queue_file = Path("data/sync_queue.json")
            queue_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(queue_file, 'w') as f:
                json.dump(self.sync_queue, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save sync queue: {e}")
    
    def _load_sync_queue(self):
        """Load sync queue from disk"""
        try:
            queue_file = Path("data/sync_queue.json")
            if queue_file.exists():
                with open(queue_file, 'r') as f:
                    self.sync_queue = json.load(f)
                    logger.info(f"Loaded {len(self.sync_queue)} items from sync queue")
        except Exception as e:
            logger.error(f"Failed to load sync queue: {e}")
            self.sync_queue = []
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        token = self.user_data.get('token')
        if not token:
            raise Exception("No authentication token available")
        
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def _sync_blink_data(self, sync_item: Dict) -> bool:
        """Sync individual blink data item"""
        try:
            session_data = sync_item['data']
            
            # Format data for API
            api_data = {
                'session_id': session_data['session_id'],
                'blink_count': session_data['total_blinks'],
                'blink_rate_per_minute': session_data['blink_rate'],
                'session_duration_seconds': session_data['duration_seconds'],
                'timestamp': session_data['timestamp'],
                'device_id': 'wellness_standalone',
                'metadata': {
                    'app_version': '1.0.0',
                    'sync_timestamp': datetime.now().isoformat()
                }
            }
            
            # Send to API
            url = f"{self.api_base_url}/api/blink-data"
            response = requests.post(
                url,
                json=api_data,
                headers=self._get_auth_headers(),
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully synced session {session_data['session_id']}")
                return True
            else:
                logger.error(f"API error {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error during sync: {e}")
            return False
        except Exception as e:
            logger.error(f"Sync error: {e}")
            return False
    
    def run(self):
        """Main sync process"""
        try:
            self.sync_started.emit()
            
            # Load any pending items from disk
            self._load_sync_queue()
            
            if not self.sync_queue:
                self.sync_completed.emit(True, "No data to sync")
                return
            
            total_items = len(self.sync_queue)
            synced_items = 0
            failed_items = []
            
            logger.info(f"Starting sync of {total_items} items")
            
            for i, sync_item in enumerate(self.sync_queue.copy()):
                self.sync_progress.emit(i + 1, total_items)
                
                success = False
                retry_count = sync_item.get('retry_count', 0)
                
                # Retry logic
                while retry_count < self.max_retries and not success:
                    if sync_item['type'] == 'blink_session':
                        success = self._sync_blink_data(sync_item)
                    
                    if not success:
                        retry_count += 1
                        if retry_count < self.max_retries:
                            logger.info(f"Retrying sync in {self.retry_delay}s (attempt {retry_count})")
                            time.sleep(self.retry_delay)
                
                if success:
                    synced_items += 1
                    self.sync_queue.remove(sync_item)
                else:
                    # Update retry count and keep in queue
                    sync_item['retry_count'] = retry_count
                    failed_items.append(sync_item)
            
            # Save updated queue (with failed items)
            self._save_sync_queue()
            
            # Report results
            if failed_items:
                message = f"Synced {synced_items}/{total_items} items. {len(failed_items)} failed."
                self.sync_completed.emit(False, message)
            else:
                message = f"Successfully synced all {synced_items} items"
                self.sync_completed.emit(True, message)
            
            logger.info(f"Sync completed: {message}")
            
        except Exception as e:
            error_msg = f"Sync process failed: {e}"
            logger.error(error_msg)
            self.sync_completed.emit(False, error_msg)
