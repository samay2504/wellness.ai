"""
Storage manager for Wellness at Work
Handles AWS S3 storage operations
"""

import json
import logging
import boto3
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError, NoCredentialsError

from models import BlinkEvent, SyncHistory

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages cloud storage operations"""
    
    def __init__(self, bucket_name: str = "wellness-ai-data", region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = None
        self._init_s3_client()
    
    def _init_s3_client(self):
        """Initialize S3 client"""
        try:
            self.s3_client = boto3.client('s3', region_name=self.region)
            # Test connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 client initialized for bucket: {self.bucket_name}")
        except NoCredentialsError:
            logger.warning("AWS credentials not found. Cloud storage disabled.")
            self.s3_client = None
        except ClientError as e:
            logger.error(f"Failed to connect to S3: {e}")
            self.s3_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing S3: {e}")
            self.s3_client = None
    
    def store_event(self, event: BlinkEvent) -> bool:
        """Store a blink event in S3 or fallback to DB"""
        if not self.s3_client:
            # Fallback: store in DB
            try:
                from .models import db
                db.session.add(event)
                db.session.commit()
                logger.info(f"Event stored locally in DB: {event.id}")
                return True
            except Exception as e:
                logger.error(f"Failed to store event in DB: {e}")
                return False
        
        try:
            # Create event data
            event_data = {
                'id': event.id,
                'user_id': event.user_id,
                'timestamp': event.timestamp,
                'count': event.count,
                'session_id': event.session_id,
                'device_id': event.device_id,
                'stored_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Generate S3 key
            date_str = datetime.fromtimestamp(event.timestamp).strftime("%Y/%m/%d")
            key = f"events/{event.user_id}/{date_str}/{event.id}.json"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(event_data, indent=2),
                ContentType='application/json'
            )
            
            logger.debug(f"Event stored in S3: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store event in S3: {e}")
            return False
    
    def store_batch_events(self, events: List[BlinkEvent]) -> bool:
        """Store multiple events as a batch in S3 or fallback to DB"""
        if not self.s3_client:
            try:
                from .models import db
                db.session.add_all(events)
                db.session.commit()
                logger.info(f"Batch stored locally in DB: {len(events)} events")
                return True
            except Exception as e:
                logger.error(f"Failed to store batch in DB: {e}")
                return False
        
        try:
            # Create batch data
            batch_data = {
                'batch_id': f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'event_count': len(events),
                'events': []
            }
            
            for event in events:
                event_data = {
                    'id': event.id,
                    'user_id': event.user_id,
                    'timestamp': event.timestamp,
                    'count': event.count,
                    'session_id': event.session_id,
                    'device_id': event.device_id
                }
                batch_data['events'].append(event_data)
            
            # Generate S3 key
            date_str = datetime.now(timezone.utc).strftime("%Y/%m/%d")
            key = f"batches/{date_str}/{batch_data['batch_id']}.json"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(batch_data, indent=2),
                ContentType='application/json'
            )
            
            logger.info(f"Batch stored in S3: {key} ({len(events)} events)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store batch in S3: {e}")
            return False
    
    def retrieve_user_events(self, user_id: int, start_date: Optional[str] = None, 
                           end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve events for a specific user from S3 or fallback to DB"""
        if not self.s3_client:
            try:
                from .models import BlinkEvent
                query = BlinkEvent.query.filter_by(user_id=user_id)
                if start_date:
                    query = query.filter(BlinkEvent.timestamp >= float(datetime.strptime(start_date, "%Y-%m-%d").timestamp()))
                if end_date:
                    query = query.filter(BlinkEvent.timestamp <= float(datetime.strptime(end_date, "%Y-%m-%d").timestamp()))
                events = [e.to_dict() for e in query.order_by(BlinkEvent.timestamp).all()]
                logger.info(f"Retrieved {len(events)} events for user {user_id} from DB")
                return events
            except Exception as e:
                logger.error(f"Failed to retrieve events from DB: {e}")
                return []
        
        try:
            events = []
            prefix = f"events/{user_id}/"
            
            # List objects in user's event directory
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
            
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        # Download and parse event
                        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=obj['Key'])
                        event_data = json.loads(response['Body'].read())
                        
                        # Apply date filters if specified
                        if start_date or end_date:
                            event_timestamp = event_data['timestamp']
                            event_date = datetime.fromtimestamp(event_timestamp).strftime("%Y-%m-%d")
                            
                            if start_date and event_date < start_date:
                                continue
                            if end_date and event_date > end_date:
                                continue
                        
                        events.append(event_data)
            
            # Sort by timestamp
            events.sort(key=lambda x: x['timestamp'])
            
            logger.info(f"Retrieved {len(events)} events for user {user_id}")
            return events
            
        except Exception as e:
            logger.error(f"Failed to retrieve events from S3: {e}")
            return []
    
    def store_sync_history(self, sync_record: SyncHistory) -> bool:
        """Store sync history in S3 or fallback to DB"""
        if not self.s3_client:
            try:
                from .models import db
                db.session.add(sync_record)
                db.session.commit()
                logger.info(f"Sync history stored locally in DB: {sync_record.id}")
                return True
            except Exception as e:
                logger.error(f"Failed to store sync history in DB: {e}")
                return False
        
        try:
            # Create sync data
            sync_data = {
                'id': sync_record.id,
                'user_id': sync_record.user_id,
                'timestamp': sync_record.timestamp,
                'events_synced': sync_record.events_synced,
                'success': sync_record.success,
                'error_message': sync_record.error_message,
                'stored_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Generate S3 key
            date_str = datetime.fromtimestamp(sync_record.timestamp).strftime("%Y/%m/%d")
            key = f"sync_history/{sync_record.user_id}/{date_str}/{sync_record.id}.json"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(sync_data, indent=2),
                ContentType='application/json'
            )
            
            logger.debug(f"Sync history stored in S3: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store sync history in S3: {e}")
            return False
    
    def delete_user_data(self, user_id: int) -> bool:
        """Delete all data for a specific user from S3 or fallback to DB"""
        if not self.s3_client:
            try:
                from .models import db, BlinkEvent, SyncHistory
                BlinkEvent.query.filter_by(user_id=user_id).delete()
                SyncHistory.query.filter_by(user_id=user_id).delete()
                db.session.commit()
                logger.info(f"Deleted all local data for user {user_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete user data from DB: {e}")
                return False
        
        try:
            # List all objects for the user
            user_prefixes = [
                f"events/{user_id}/",
                f"batches/",  # Will need to filter by user_id in batch content
                f"sync_history/{user_id}/"
            ]
            
            objects_to_delete = []
            
            for prefix in user_prefixes:
                paginator = self.s3_client.get_paginator('list_objects_v2')
                page_iterator = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
                
                for page in page_iterator:
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            # For batches, check if they contain user's data
                            if prefix == "batches/":
                                try:
                                    response = self.s3_client.get_object(Bucket=self.bucket_name, Key=obj['Key'])
                                    batch_data = json.loads(response['Body'].read())
                                    if any(event.get('user_id') == user_id for event in batch_data.get('events', [])):
                                        objects_to_delete.append({'Key': obj['Key']})
                                except Exception:
                                    # If we can't read the batch, skip it
                                    continue
                            else:
                                objects_to_delete.append({'Key': obj['Key']})
            
            # Delete objects in batches of 1000 (S3 limit)
            batch_size = 1000
            for i in range(0, len(objects_to_delete), batch_size):
                batch = objects_to_delete[i:i + batch_size]
                if batch:
                    self.s3_client.delete_objects(
                        Bucket=self.bucket_name,
                        Delete={'Objects': batch}
                    )
            
            logger.info(f"Deleted {len(objects_to_delete)} objects for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user data from S3: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        if not self.s3_client:
            return {'error': 'S3 client not available'}
        
        try:
            stats = {
                'total_objects': 0,
                'total_size_bytes': 0,
                'events_count': 0,
                'batches_count': 0,
                'sync_history_count': 0
            }
            
            # Count objects by type
            prefixes = ['events/', 'batches/', 'sync_history/']
            
            for prefix in prefixes:
                paginator = self.s3_client.get_paginator('list_objects_v2')
                page_iterator = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
                
                for page in page_iterator:
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            stats['total_objects'] += 1
                            stats['total_size_bytes'] += obj['Size']
                            
                            if prefix == 'events/':
                                stats['events_count'] += 1
                            elif prefix == 'batches/':
                                stats['batches_count'] += 1
                            elif prefix == 'sync_history/':
                                stats['sync_history_count'] += 1
            
            # Convert bytes to MB
            stats['total_size_mb'] = round(stats['total_size_bytes'] / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {'error': str(e)}
    
    def is_available(self) -> bool:
        """Check if cloud storage is available"""
        return self.s3_client is not None
    
    def create_backup(self, backup_name: str) -> bool:
        """Create a backup of all data"""
        if not self.s3_client:
            logger.warning("S3 client not available")
            return False
        
        try:
            # Create backup manifest
            backup_manifest = {
                'backup_name': backup_name,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'objects': []
            }
            
            # List all objects
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=self.bucket_name)
            
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        backup_manifest['objects'].append({
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'].isoformat()
                        })
            
            # Store backup manifest
            backup_key = f"backups/{backup_name}/manifest.json"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=backup_key,
                Body=json.dumps(backup_manifest, indent=2),
                ContentType='application/json'
            )
            
            logger.info(f"Backup manifest created: {backup_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False 