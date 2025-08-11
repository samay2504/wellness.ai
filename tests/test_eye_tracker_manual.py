#!/usr/bin/env python3
"""
Simple test script to verify MediaPipe eye tracking functionality
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from desktop_app.eye_tracker import create_eye_tracker

def main():
    print("=== MediaPipe Eye Tracker Test ===")
    
    # Create eye tracker
    tracker = create_eye_tracker()
    print(f"✓ Eye tracker created - Session: {tracker.session_id}")
    
    # Start tracking
    print("Starting camera...")
    success = tracker.start_tracking()
    print(f"✓ Camera started: {success}")
    
    if not success:
        print("❌ Failed to start camera")
        return
    
    try:
        # Test for 5 seconds
        print("Testing for 5 seconds... Please blink naturally")
        initial_count = tracker.get_current_blink_count()
        print(f"Initial blink count: {initial_count}")
        
        time.sleep(5)
        
        final_count = tracker.get_current_blink_count()
        print(f"Final blink count: {final_count}")
        print(f"Blinks detected: {final_count - initial_count}")
        
        # Get statistics
        stats = tracker.get_stats()
        print(f"✓ Statistics: {stats}")
        
    finally:
        # Stop tracking
        tracker.stop_tracking()
        print("✓ Camera stopped successfully")
    
    print("=== Test Completed ===")

if __name__ == "__main__":
    main()
