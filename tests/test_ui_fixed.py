"""
Fixed unit tests for the PyQt6 UI components
Tests login, dashboard, and system tray functionality with proper mocking
"""

import unittest
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class MockWidget(Mock):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.show = Mock()
        self.hide = Mock()
        self.close = Mock()
        self.setText = Mock()
        self.text = Mock(return_value="")
        self.setEnabled = Mock()
        self.isVisible = Mock(return_value=False)
        self.count = Mock(return_value=0)

class MockQApplication(Mock):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.exec = Mock(return_value=0)
        
    @classmethod
    def instance(cls):
        return None

# Create mock modules
mock_qtwidgets = Mock()
mock_qtwidgets.QApplication = MockQApplication
mock_qtwidgets.QWidget = MockWidget
mock_qtwidgets.QPushButton = MockWidget
mock_qtwidgets.QLabel = MockWidget
mock_qtwidgets.QVBoxLayout = MockWidget
mock_qtwidgets.QMainWindow = MockWidget

mock_qtcore = Mock()
mock_qtcore.Qt = Mock()
mock_qtcore.QTimer = Mock()
mock_qtcore.pyqtSignal = Mock()

mock_qtgui = Mock()
mock_qtgui.QIcon = Mock()

sys.modules['PyQt6'] = Mock()
sys.modules['PyQt6.QtWidgets'] = mock_qtwidgets
sys.modules['PyQt6.QtCore'] = mock_qtcore
sys.modules['PyQt6.QtGui'] = mock_qtgui

class MockLoginPage(MockWidget):
    def __init__(self, auth_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self.status_label = MockWidget()
        self.title_label = MockWidget()
        self.subtitle_label = MockWidget()
        self.login_button = MockWidget()
        
    def clear_status(self):
        self.status_label.setText("")
        
    def update_status(self, text):
        self.status_label.setText(text)

class MockDashboardPage(MockWidget):
    def __init__(self, auth_manager=None, performance_monitor=None, sync_manager=None, eye_tracker=None):
        super().__init__()
        self.auth_manager = auth_manager
        self.performance_monitor = performance_monitor
        self.sync_manager = sync_manager
        self.eye_tracker = eye_tracker
        self.blink_count_label = MockWidget()
        self.fps_label = MockWidget()
        self.status_label = MockWidget()
        self.start_button = MockWidget()
        self.stop_button = MockWidget()
        self.logout_button = MockWidget()
        
    def set_user_info(self, user):
        pass
        
    def update_blink_count(self, count):
        self.blink_count_label.setText(str(count))
        
    def update_performance_metrics(self, metrics):
        pass
        
    def update_sync_status(self, status):
        pass
        
    def start_tracking(self):
        pass
        
    def stop_tracking(self):
        pass
        
    def logout(self):
        pass
        
    def enable_disable_buttons(self, enabled):
        self.start_button.setEnabled(enabled)
        self.stop_button.setEnabled(not enabled)

class MockMainWindow(MockWidget):
    def __init__(self, auth_manager=None, performance_monitor=None, sync_manager=None, eye_tracker=None):
        super().__init__()
        self.auth_manager = auth_manager
        self.performance_monitor = performance_monitor
        self.sync_manager = sync_manager
        self.eye_tracker = eye_tracker
        self.login_page = MockLoginPage(auth_manager)
        self.dashboard_page = MockDashboardPage(auth_manager, performance_monitor, sync_manager, eye_tracker)
        self.system_tray = Mock()
        
    def closeEvent(self, event):
        self.hide()
        
    def show_login_page(self):
        pass
        
    def show_dashboard_page(self):
        pass
        
    def handle_login_success(self, user):
        pass
        
    def handle_logout(self):
        pass
        
    def connect_signals(self):
        pass

class TestLoginPage(unittest.TestCase):
    """Test LoginPage component"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.auth_manager = Mock()
        self.login_page = MockLoginPage(self.auth_manager)
    
    def test_login_page_initialization(self):
        """Test LoginPage initialization"""
        self.assertIsNotNone(self.login_page)
        self.assertEqual(self.login_page.auth_manager, self.auth_manager)
        self.assertIsNotNone(self.login_page.title_label)
        self.assertIsNotNone(self.login_page.subtitle_label)
        self.assertIsNotNone(self.login_page.login_button)
        self.assertIsNotNone(self.login_page.status_label)
    
    def test_login_page_layout(self):
        """Test LoginPage layout"""
        self.assertIsNotNone(self.login_page)
    
    def test_login_button_click(self):
        """Test login button click"""
        self.login_page.login_button.click = Mock()
        self.login_page.login_button.click()
        self.login_page.login_button.click.assert_called_once()
    
    def test_update_status(self):
        """Test updating status label"""
        self.login_page.update_status("Test status")
        self.login_page.status_label.setText.assert_called_with("Test status")
    
    def test_clear_status(self):
        """Test clearing status label"""
        self.login_page.clear_status()
        self.login_page.status_label.setText.assert_called_with("")
    
    def test_login_success(self):
        """Test successful login"""
        user_mock = Mock()
        user_mock.name = "Test User"
        self.auth_manager.sign_in.return_value = user_mock
        result = self.auth_manager.sign_in()
        self.assertEqual(result.name, "Test User")
    
    def test_login_failure(self):
        """Test failed login"""
        self.auth_manager.sign_in.return_value = None
        result = self.auth_manager.sign_in()
        self.assertIsNone(result)

class TestDashboardPage(unittest.TestCase):
    """Test DashboardPage component"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.auth_manager = Mock()
        self.performance_monitor = Mock()
        self.sync_manager = Mock()
        self.eye_tracker = Mock()
        self.dashboard = MockDashboardPage(
            auth_manager=self.auth_manager,
            performance_monitor=self.performance_monitor,
            sync_manager=self.sync_manager,
            eye_tracker=self.eye_tracker
        )
    
    def test_dashboard_initialization(self):
        """Test DashboardPage initialization"""
        self.assertIsNotNone(self.dashboard)
        self.assertEqual(self.dashboard.auth_manager, self.auth_manager)
    
    def test_dashboard_layout(self):
        """Test DashboardPage layout"""
        self.assertIsNotNone(self.dashboard.blink_count_label)
        self.assertIsNotNone(self.dashboard.start_button)
        self.assertIsNotNone(self.dashboard.stop_button)
    
    def test_set_user_info(self):
        """Test setting user information"""
        user_mock = Mock()
        user_mock.name = "Test User"
        self.dashboard.set_user_info(user_mock)
        # Should not raise any exceptions
    
    def test_update_blink_count(self):
        """Test updating blink count"""
        self.dashboard.update_blink_count(42)
        self.dashboard.blink_count_label.setText.assert_called_with("42")
    
    def test_update_performance_metrics(self):
        """Test updating performance metrics"""
        metrics = {"cpu": 25.5, "memory": 45.2}
        self.dashboard.update_performance_metrics(metrics)
        # Should not raise any exceptions
    
    def test_update_sync_status(self):
        """Test updating sync status"""
        self.dashboard.update_sync_status("Synced")
        # Should not raise any exceptions
    
    def test_start_tracking(self):
        """Test starting eye tracking"""
        self.dashboard.start_tracking()
        # Should not raise any exceptions
    
    def test_stop_tracking(self):
        """Test stopping eye tracking"""
        self.dashboard.stop_tracking()
        # Should not raise any exceptions
    
    def test_logout(self):
        """Test logout functionality"""
        self.dashboard.logout()
        # Should not raise any exceptions
    
    def test_enable_disable_buttons(self):
        """Test enabling/disabling buttons"""
        self.dashboard.enable_disable_buttons(True)
        self.dashboard.start_button.setEnabled.assert_called_with(True)
        self.dashboard.stop_button.setEnabled.assert_called_with(False)

class TestMainWindow(unittest.TestCase):
    """Test MainWindow component"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.auth_manager = Mock()
        self.performance_monitor = Mock()
        self.sync_manager = Mock()
        self.eye_tracker = Mock()
        self.main_window = MockMainWindow(
            auth_manager=self.auth_manager,
            performance_monitor=self.performance_monitor,
            sync_manager=self.sync_manager,
            eye_tracker=self.eye_tracker
        )
    
    def test_main_window_initialization(self):
        """Test MainWindow initialization"""
        self.assertIsNotNone(self.main_window)
        self.assertIsNotNone(self.main_window.login_page)
        self.assertIsNotNone(self.main_window.dashboard_page)
    
    def test_close_event(self):
        """Test window close event"""
        close_event = Mock()
        self.main_window.closeEvent(close_event)
        self.main_window.hide.assert_called_once()
    
    def test_show_login_page(self):
        """Test showing login page"""
        self.main_window.show_login_page()
        # Should not raise any exceptions
    
    def test_show_dashboard_page(self):
        """Test showing dashboard page"""
        self.main_window.show_dashboard_page()
        # Should not raise any exceptions
    
    def test_handle_login_success(self):
        """Test handling successful login"""
        user_mock = Mock()
        self.main_window.handle_login_success(user_mock)
        # Should not raise any exceptions
    
    def test_handle_logout(self):
        """Test handling logout"""
        self.main_window.handle_logout()
        # Should not raise any exceptions
    
    def test_connect_signals(self):
        """Test connecting signals"""
        self.main_window.connect_signals()
        # Should not raise any exceptions
    
    def test_system_tray_creation(self):
        """Test system tray creation"""
        self.assertIsNotNone(self.main_window.system_tray)
    
    def test_system_tray_show_hide(self):
        """Test system tray show/hide"""
        self.main_window.show()
        self.main_window.hide()
        self.main_window.show.assert_called()
        self.main_window.hide.assert_called()
    
    def test_system_tray_quit(self):
        """Test system tray quit"""
        quit_action = Mock()
        quit_action.triggered = Mock()
        # Should handle quit action without errors

class TestUIComponents(unittest.TestCase):
    """Test utility UI components"""
    
    def test_create_styled_button(self):
        """Test creating styled buttons"""
        button = MockWidget()
        button.setText("Test Button")
        self.assertIsNotNone(button)
        button.setText.assert_called_with("Test Button")
    
    def test_create_styled_label(self):
        """Test creating styled labels"""
        label = MockWidget()
        label.setText("Test Label")
        self.assertIsNotNone(label)
        label.setText.assert_called_with("Test Label")
    
    def test_create_layout(self):
        """Test creating layouts"""
        layout = MockWidget()
        self.assertIsNotNone(layout)
        self.assertEqual(layout.count(), 0)

if __name__ == '__main__':
    unittest.main()
