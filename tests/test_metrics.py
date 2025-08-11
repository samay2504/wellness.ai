"""
Unit tests for the performance monitoring module
Tests system metrics collection and monitoring functionality
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from desktop_app.metrics import PerformanceMonitor, SystemMetrics


class TestSystemMetrics(unittest.TestCase):
    """Test SystemMetrics dataclass"""
    
    def test_system_metrics_creation(self):
        """Test creating SystemMetrics"""
        metrics = SystemMetrics(
            cpu_percent=25.5,
            memory_percent=45.2,
            memory_used=2048576,
            memory_total=8589934592,
            disk_usage_percent=30.1,
            disk_used=3221225472,
            disk_total=10737418240,
            network_sent=1048576,
            network_recv=2097152,
            timestamp=1640995200.0
        )
        
        self.assertEqual(metrics.cpu_percent, 25.5)
        self.assertEqual(metrics.memory_percent, 45.2)
        self.assertEqual(metrics.memory_used, 2048576)
        self.assertEqual(metrics.memory_total, 8589934592)
        self.assertEqual(metrics.disk_usage_percent, 30.1)
        self.assertEqual(metrics.disk_used, 3221225472)
        self.assertEqual(metrics.disk_total, 10737418240)
        self.assertEqual(metrics.network_sent, 1048576)
        self.assertEqual(metrics.network_recv, 2097152)
        self.assertEqual(metrics.timestamp, 1640995200.0)
    
    def test_system_metrics_to_dict(self):
        """Test converting SystemMetrics to dictionary"""
        metrics = SystemMetrics(
            cpu_percent=15.3,
            memory_percent=60.7,
            memory_used=5242880,
            memory_total=8589934592,
            disk_usage_percent=25.0,
            disk_used=2684354560,
            disk_total=10737418240,
            network_sent=524288,
            network_recv=1048576,
            timestamp=1640995200.0
        )
        
        metrics_dict = metrics.to_dict()
        
        self.assertEqual(metrics_dict["cpu_percent"], 15.3)
        self.assertEqual(metrics_dict["memory_percent"], 60.7)
        self.assertEqual(metrics_dict["memory_used"], 5242880)
        self.assertEqual(metrics_dict["memory_total"], 8589934592)
        self.assertEqual(metrics_dict["disk_usage_percent"], 25.0)
        self.assertEqual(metrics_dict["disk_used"], 2684354560)
        self.assertEqual(metrics_dict["disk_total"], 10737418240)
        self.assertEqual(metrics_dict["network_sent"], 524288)
        self.assertEqual(metrics_dict["network_recv"], 1048576)
        self.assertEqual(metrics_dict["timestamp"], 1640995200.0)
    
    def test_system_metrics_from_dict(self):
        """Test creating SystemMetrics from dictionary"""
        metrics_dict = {
            "cpu_percent": 35.8,
            "memory_percent": 55.2,
            "memory_used": 4718592,
            "memory_total": 8589934592,
            "disk_usage_percent": 40.5,
            "disk_used": 4294967296,
            "disk_total": 10737418240,
            "network_sent": 1572864,
            "network_recv": 3145728,
            "timestamp": 1640995200.0
        }
        
        metrics = SystemMetrics.from_dict(metrics_dict)
        
        self.assertEqual(metrics.cpu_percent, 35.8)
        self.assertEqual(metrics.memory_percent, 55.2)
        self.assertEqual(metrics.memory_used, 4718592)
        self.assertEqual(metrics.memory_total, 8589934592)
        self.assertEqual(metrics.disk_usage_percent, 40.5)
        self.assertEqual(metrics.disk_used, 4294967296)
        self.assertEqual(metrics.disk_total, 10737418240)
        self.assertEqual(metrics.network_sent, 1572864)
        self.assertEqual(metrics.network_recv, 3145728)
        self.assertEqual(metrics.timestamp, 1640995200.0)


class TestPerformanceMonitor(unittest.TestCase):
    """Test PerformanceMonitor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.monitor = PerformanceMonitor()
    
    def tearDown(self):
        """Clean up after tests"""
        if self.monitor.is_running:
            self.monitor.stop()
    
    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initialization"""
        self.assertFalse(self.monitor.is_running)
        self.assertIsNone(self.monitor.monitoring_thread)
        self.assertEqual(len(self.monitor.metrics_history), 0)
        self.assertIsInstance(self.monitor.update_interval, float)
        self.assertGreater(self.monitor.update_interval, 0)
    
    def test_start_monitoring(self):
        """Test starting performance monitoring"""
        # Mock threading.Thread in the source module
        with patch('src.desktop_app.metrics.Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            result = self.monitor.start()
            
            self.assertTrue(result)
            self.assertTrue(self.monitor.is_running)
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
    
    def test_stop_monitoring(self):
        """Test stopping performance monitoring"""
        # Set up running state
        self.monitor.is_running = True
        self.monitor.monitoring_thread = Mock()
        
        self.monitor.stop()
        
        self.assertFalse(self.monitor.is_running)
        self.monitor.monitoring_thread.join.assert_called_once()
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    def test_collect_system_metrics(self, mock_net_io, mock_disk, mock_memory, mock_cpu):
        """Test collecting system metrics"""
        # Mock psutil functions
        mock_cpu.return_value = 25.5
        
        mock_memory_obj = Mock()
        mock_memory_obj.percent = 45.2
        mock_memory_obj.used = 2048576
        mock_memory_obj.total = 8589934592
        mock_memory.return_value = mock_memory_obj
        
        mock_disk_obj = Mock()
        mock_disk_obj.percent = 30.1
        mock_disk_obj.used = 3221225472
        mock_disk_obj.total = 10737418240
        mock_disk.return_value = mock_disk_obj
        
        mock_net_obj = Mock()
        mock_net_obj.bytes_sent = 1048576
        mock_net_obj.bytes_recv = 2097152
        mock_net_io.return_value = mock_net_obj
        
        # Collect metrics
        metrics = self.monitor._collect_system_metrics()
        
        self.assertIsInstance(metrics, SystemMetrics)
        self.assertEqual(metrics.cpu_percent, 25.5)
        self.assertEqual(metrics.memory_percent, 45.2)
        self.assertEqual(metrics.memory_used, 2048576)
        self.assertEqual(metrics.memory_total, 8589934592)
        self.assertEqual(metrics.disk_usage_percent, 30.1)
        self.assertEqual(metrics.disk_used, 3221225472)
        self.assertEqual(metrics.disk_total, 10737418240)
        self.assertEqual(metrics.network_sent, 1048576)
        self.assertEqual(metrics.network_recv, 2097152)
        self.assertIsInstance(metrics.timestamp, float)
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    def test_collect_system_metrics_with_exceptions(self, mock_net_io, mock_disk, mock_memory, mock_cpu):
        """Test collecting system metrics with exceptions"""
        # Mock exceptions
        mock_cpu.side_effect = Exception("CPU error")
        mock_memory.side_effect = Exception("Memory error")
        mock_disk.side_effect = Exception("Disk error")
        mock_net_io.side_effect = Exception("Network error")
        
        # Collect metrics (should handle exceptions gracefully)
        metrics = self.monitor._collect_system_metrics()
        
        self.assertIsInstance(metrics, SystemMetrics)
        # Should have default values when exceptions occur
        self.assertEqual(metrics.cpu_percent, 0.0)
        self.assertEqual(metrics.memory_percent, 0.0)
        self.assertEqual(metrics.memory_used, 0)
        self.assertEqual(metrics.memory_total, 0)
        self.assertEqual(metrics.disk_usage_percent, 0.0)
        self.assertEqual(metrics.disk_used, 0)
        self.assertEqual(metrics.disk_total, 0)
        self.assertEqual(metrics.network_sent, 0)
        self.assertEqual(metrics.network_recv, 0)
    
    def test_get_current_metrics(self):
        """Test getting current metrics"""
        # Mock a metrics object
        mock_metrics = SystemMetrics(
            cpu_percent=20.0,
            memory_percent=50.0,
            memory_used=4294967296,
            memory_total=8589934592,
            disk_usage_percent=25.0,
            disk_used=2684354560,
            disk_total=10737418240,
            network_sent=524288,
            network_recv=1048576,
            timestamp=time.time()
        )
        
        # Set current metrics
        self.monitor.current_metrics = mock_metrics
        
        current = self.monitor.get_current_metrics()
        
        self.assertEqual(current, mock_metrics)
    
    def test_get_metrics_history(self):
        """Test getting metrics history"""
        # Add some test metrics to history
        test_metrics = [
            SystemMetrics(cpu_percent=10.0, memory_percent=40.0, memory_used=3435973836, memory_total=8589934592, disk_usage_percent=20.0, disk_used=2147483648, disk_total=10737418240, network_sent=262144, network_recv=524288, timestamp=time.time() - 60),
            SystemMetrics(cpu_percent=15.0, memory_percent=45.0, memory_used=3865470566, memory_total=8589934592, disk_usage_percent=22.0, disk_used=2362232012, disk_total=10737418240, network_sent=393216, network_recv=786432, timestamp=time.time() - 30),
            SystemMetrics(cpu_percent=20.0, memory_percent=50.0, memory_used=4294967296, memory_total=8589934592, disk_usage_percent=25.0, disk_used=2684354560, disk_total=10737418240, network_sent=524288, network_recv=1048576, timestamp=time.time())
        ]
        
        self.monitor.metrics_history = test_metrics
        
        history = self.monitor.get_metrics_history()
        
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0].cpu_percent, 10.0)
        self.assertEqual(history[1].cpu_percent, 15.0)
        self.assertEqual(history[2].cpu_percent, 20.0)
    
    def test_get_metrics_history_with_limit(self):
        """Test getting metrics history with limit"""
        # Add many test metrics
        test_metrics = []
        for i in range(100):
            metrics = SystemMetrics(
                cpu_percent=float(i),
                memory_percent=40.0,
                memory_used=3435973836,
                memory_total=8589934592,
                disk_usage_percent=20.0,
                disk_used=2147483648,
                disk_total=10737418240,
                network_sent=262144,
                network_recv=524288,
                timestamp=time.time() - (100 - i)
            )
            test_metrics.append(metrics)
        
        self.monitor.metrics_history = test_metrics
        
        # Get last 10 metrics
        history = self.monitor.get_metrics_history(limit=10)
        
        self.assertEqual(len(history), 10)
        self.assertEqual(history[0].cpu_percent, 90.0)  # Most recent
        self.assertEqual(history[9].cpu_percent, 81.0)  # 10th most recent
    
    def test_get_average_metrics(self):
        """Test getting average metrics"""
        # Add test metrics
        test_metrics = [
            SystemMetrics(cpu_percent=10.0, memory_percent=40.0, memory_used=3435973836, memory_total=8589934592, disk_usage_percent=20.0, disk_used=2147483648, disk_total=10737418240, network_sent=262144, network_recv=524288, timestamp=time.time() - 60),
            SystemMetrics(cpu_percent=20.0, memory_percent=50.0, memory_used=4294967296, memory_total=8589934592, disk_usage_percent=25.0, disk_used=2684354560, disk_total=10737418240, network_sent=524288, network_recv=1048576, timestamp=time.time() - 30),
            SystemMetrics(cpu_percent=30.0, memory_percent=60.0, memory_used=5153960755, memory_total=8589934592, disk_usage_percent=30.0, disk_used=3221225472, disk_total=10737418240, network_sent=786432, network_recv=1572864, timestamp=time.time())
        ]
        
        self.monitor.metrics_history = test_metrics
        
        averages = self.monitor.get_average_metrics()
        
        self.assertEqual(averages["cpu_percent"], 20.0)  # (10 + 20 + 30) / 3
        self.assertEqual(averages["memory_percent"], 50.0)  # (40 + 50 + 60) / 3
        self.assertEqual(averages["disk_usage_percent"], 25.0)  # (20 + 25 + 30) / 3
    
    def test_get_peak_metrics(self):
        """Test getting peak metrics"""
        # Add test metrics
        test_metrics = [
            SystemMetrics(cpu_percent=10.0, memory_percent=40.0, memory_used=3435973836, memory_total=8589934592, disk_usage_percent=20.0, disk_used=2147483648, disk_total=10737418240, network_sent=262144, network_recv=524288, timestamp=time.time() - 60),
            SystemMetrics(cpu_percent=50.0, memory_percent=80.0, memory_used=6871947673, memory_total=8589934592, disk_usage_percent=60.0, disk_used=6442450944, disk_total=10737418240, network_sent=2097152, network_recv=4194304, timestamp=time.time() - 30),
            SystemMetrics(cpu_percent=30.0, memory_percent=60.0, memory_used=5153960755, memory_total=8589934592, disk_usage_percent=30.0, disk_used=3221225472, disk_total=10737418240, network_sent=786432, network_recv=1572864, timestamp=time.time())
        ]
        
        self.monitor.metrics_history = test_metrics
        
        peaks = self.monitor.get_peak_metrics()
        
        self.assertEqual(peaks["cpu_percent"], 50.0)  # Maximum CPU
        self.assertEqual(peaks["memory_percent"], 80.0)  # Maximum memory
        self.assertEqual(peaks["disk_usage_percent"], 60.0)  # Maximum disk usage
        self.assertEqual(peaks["network_sent"], 2097152)  # Maximum network sent
        self.assertEqual(peaks["network_recv"], 4194304)  # Maximum network received
    
    def test_get_process_metrics(self):
        """Test getting process-specific metrics"""
        # Mock psutil.Process
        with patch('psutil.Process') as mock_process_class:
            mock_process = Mock()
            mock_process.cpu_percent.return_value = 5.5
            mock_process.memory_percent.return_value = 2.3
            mock_process.memory_info.return_value = Mock(rss=1048576, vms=2097152)
            mock_process.num_threads.return_value = 4
            mock_process.create_time.return_value = time.time() - 3600  # 1 hour ago
            mock_process_class.return_value = mock_process
            
            metrics = self.monitor.get_process_metrics(12345)
            
            self.assertEqual(metrics["cpu_percent"], 5.5)
            self.assertEqual(metrics["memory_percent"], 2.3)
            self.assertEqual(metrics["memory_rss"], 1048576)
            self.assertEqual(metrics["memory_vms"], 2097152)
            self.assertEqual(metrics["num_threads"], 4)
            self.assertIn("uptime", metrics)
    
    def test_get_process_metrics_invalid_pid(self):
        """Test getting process metrics with invalid PID"""
        with patch('psutil.Process') as mock_process_class:
            import psutil
            mock_process_class.side_effect = psutil.NoSuchProcess(99999)
            
            metrics = self.monitor.get_process_metrics(99999)
            
            self.assertEqual(metrics["cpu_percent"], 0.0)
            self.assertEqual(metrics["memory_percent"], 0.0)
            self.assertEqual(metrics["memory_rss"], 0)
            self.assertEqual(metrics["memory_vms"], 0)
            self.assertEqual(metrics["num_threads"], 0)
            self.assertEqual(metrics["uptime"], 0)
    
    def test_clear_history(self):
        """Test clearing metrics history"""
        # Add some test metrics
        test_metrics = [
            SystemMetrics(cpu_percent=10.0, memory_percent=40.0, memory_used=3435973836, memory_total=8589934592, disk_usage_percent=20.0, disk_used=2147483648, disk_total=10737418240, network_sent=262144, network_recv=524288, timestamp=time.time()),
            SystemMetrics(cpu_percent=20.0, memory_percent=50.0, memory_used=4294967296, memory_total=8589934592, disk_usage_percent=25.0, disk_used=2684354560, disk_total=10737418240, network_sent=524288, network_recv=1048576, timestamp=time.time())
        ]
        
        self.monitor.metrics_history = test_metrics
        
        self.monitor.clear_history()
        
        self.assertEqual(len(self.monitor.metrics_history), 0)
    
    def test_set_update_interval(self):
        """Test setting update interval"""
        new_interval = 5.0
        
        self.monitor.set_update_interval(new_interval)
        
        self.assertEqual(self.monitor.update_interval, new_interval)
    
    def test_set_update_interval_invalid(self):
        """Test setting invalid update interval"""
        # Should not allow negative or zero intervals
        self.monitor.set_update_interval(-1.0)
        self.assertGreater(self.monitor.update_interval, 0)
        
        self.monitor.set_update_interval(0.0)
        self.assertGreater(self.monitor.update_interval, 0)
    
    def test_monitoring_thread_function(self):
        """Test the monitoring thread function"""
        # Mock time.sleep to control the loop
        with patch('time.sleep') as mock_sleep:
            # Set up monitor to run for 2 iterations only
            call_count = 0
            def side_effect(*args):
                nonlocal call_count
                call_count += 1
                if call_count >= 2:
                    raise Exception("Stop")
            
            mock_sleep.side_effect = side_effect
            
            # Mock collect_system_metrics
            with patch.object(self.monitor, '_collect_system_metrics') as mock_collect:
                mock_collect.return_value = SystemMetrics(
                    cpu_percent=25.0,
                    memory_percent=50.0,
                    memory_used=4294967296,
                    memory_total=8589934592,
                    disk_usage_percent=25.0,
                    disk_used=2684354560,
                    disk_total=10737418240,
                    network_sent=524288,
                    network_recv=1048576,
                    timestamp=time.time()
                )
                
                # Set monitor to running state
                self.monitor.is_running = True
                
                # Run monitoring function
                try:
                    self.monitor._monitoring_thread_function()
                except Exception:
                    pass  # Expected to stop after 2 iterations
                
                # Verify metrics were collected exactly 2 times
                self.assertEqual(mock_collect.call_count, 2)
                self.assertEqual(len(self.monitor.metrics_history), 2)
    
    def test_export_metrics_data(self):
        """Test exporting metrics data"""
        # Add test metrics
        test_metrics = [
            SystemMetrics(cpu_percent=10.0, memory_percent=40.0, memory_used=3435973836, memory_total=8589934592, disk_usage_percent=20.0, disk_used=2147483648, disk_total=10737418240, network_sent=262144, network_recv=524288, timestamp=time.time() - 60),
            SystemMetrics(cpu_percent=20.0, memory_percent=50.0, memory_used=4294967296, memory_total=8589934592, disk_usage_percent=25.0, disk_used=2684354560, disk_total=10737418240, network_sent=524288, network_recv=1048576, timestamp=time.time())
        ]
        
        self.monitor.metrics_history = test_metrics
        
        exported_data = self.monitor.export_metrics_data()
        
        self.assertIsInstance(exported_data, dict)
        self.assertIn("metrics_history", exported_data)
        self.assertIn("summary", exported_data)
        self.assertIn("export_timestamp", exported_data)
        
        # Check metrics history
        history = exported_data["metrics_history"]
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["cpu_percent"], 10.0)
        self.assertEqual(history[1]["cpu_percent"], 20.0)
        
        # Check summary
        summary = exported_data["summary"]
        self.assertIn("total_metrics", summary)
        self.assertIn("average_cpu", summary)
        self.assertIn("average_memory", summary)
        self.assertIn("peak_cpu", summary)
        self.assertIn("peak_memory", summary)


if __name__ == '__main__':
    unittest.main() 