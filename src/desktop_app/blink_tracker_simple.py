"""
Simple blink tracker used for tests and headless environments.
Implements a minimal interface compatible with tests expecting
EyeBlinkTracker and create_blink_tracker.
"""

import time
import uuid
from dataclasses import dataclass, asdict
from typing import Callable, List, Dict, Any, Optional


@dataclass
class BlinkData:
	timestamp: float
	blink_count: int
	ear_left: float = 0.0
	ear_right: float = 0.0
	confidence: float = 1.0
	session_id: str = ""
	device_id: str = "desktop"

	def to_dict(self) -> Dict[str, Any]:
		return asdict(self)


class EyeBlinkTracker:
	def __init__(self, mock_mode: bool = True):
		self.session_id = f"session_{int(time.time())}_{uuid.uuid4().hex[:6]}"
		self.device_id = uuid.uuid4().hex[:8]
		self.blink_count = 0
		self.is_running = False
		self.mock_mode = mock_mode
		self.blink_callbacks: List[Callable[[BlinkData], None]] = []
		self.error_callbacks: List[Callable[[Exception], None]] = []
		# Backwards-compat alias used by tests
		self.callbacks = self.blink_callbacks

	# Aliases expected by tests
	def start_tracking(self) -> bool:
		return self.start()

	def stop_tracking(self) -> bool:
		self.stop()
		return True

	def start(self) -> bool:
		self.is_running = True
		return True

	def stop(self):
		self.is_running = False

	def add_blink_callback(self, cb: Callable[[BlinkData], None]):
		self.blink_callbacks.append(cb)

	def add_error_callback(self, cb: Callable[[Exception], None]):
		self.error_callbacks.append(cb)

	def get_current_blink_count(self) -> int:
		return self.blink_count

	def get_stats(self) -> Dict[str, Any]:
		return {
			"session_id": self.session_id,
			"device_id": self.device_id,
			"blink_count": self.blink_count,
			"detection_rate": 100.0,
			"is_running": self.is_running,
			"tracking_mode": "mock" if self.mock_mode else "real",
		}

	def reset_session(self):
		self.session_id = f"session_{int(time.time())}_{uuid.uuid4().hex[:6]}"
		self.blink_count = 0

def create_blink_tracker(mock_mode: bool = True, callback: Optional[Callable[[BlinkData], None]] = None) -> EyeBlinkTracker:
	tracker = EyeBlinkTracker(mock_mode=mock_mode)
	if callback:
		tracker.add_blink_callback(callback)
	return tracker

