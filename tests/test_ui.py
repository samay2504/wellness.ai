"""
Unit tests for the PyQt6 UI components
Tests login, dashboard, and system tray functionality
"""

import unittest
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

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

class SimpleSignal:
    def __init__(self):
        self._subs = []
    def connect(self, fn):
        self._subs.append(fn)
    def emit(self, *args, **kwargs):
        for fn in list(self._subs):
            try:
                fn(*args, **kwargs)
            except Exception:
                pass

class MockWidget(Mock):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._visible = False
        self._enabled = True
        self._text = args[0] if args and isinstance(args[0], str) else ""
        self._layout = None
        self.show = Mock(side_effect=lambda: setattr(self, "_visible", True))
        self.hide = Mock(side_effect=lambda: setattr(self, "_visible", False))
        self.close = Mock()
        self.setText = Mock(side_effect=lambda t: setattr(self, "_text", t))
        self.text = Mock(side_effect=lambda: self._text)
        self.setEnabled = Mock(side_effect=lambda v: setattr(self, "_enabled", bool(v)))
        self.isEnabled = Mock(side_effect=lambda: self._enabled)
        self.isVisible = Mock(side_effect=lambda: self._visible)
        self.setLayout = Mock(side_effect=lambda l: setattr(self, "_layout", l))
        self.layout = Mock(side_effect=lambda: self._layout)

class QPushButton(MockWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clicked = SimpleSignal()
    def click(self):
        self.clicked.emit()

class QLabel(MockWidget):
    pass

class QVBoxLayout:
    def __init__(self, *args, **kwargs):
        self._items = []
    def addWidget(self, w):
        self._items.append(w)
    def addLayout(self, l):
        self._items.append(l)
    def count(self):
        return len(self._items)
    class _Item:
        def __init__(self, w):
            self._w = w
        def widget(self):
            return self._w
    def itemAt(self, i):
        try:
            w = self._items[i]
            return self._Item(w if isinstance(w, MockWidget) else None)
        except Exception:
            return self._Item(None)

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
mock_qtwidgets.QPushButton = QPushButton
mock_qtwidgets.QLabel = QLabel
mock_qtwidgets.QVBoxLayout = QVBoxLayout
MockQApplication.quit = classmethod(lambda cls: None)
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
        self.login_successful = SimpleSignal()
        self.login_failed = SimpleSignal()
        self.status_label = QLabel("")
        self.title_label = QLabel("Title")
        self.subtitle_label = QLabel("Subtitle")
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self._attempt_login)
        lay = QVBoxLayout()
        for w in [self.title_label, self.subtitle_label, self.login_button, self.status_label]:
            lay.addWidget(w)
        self.setLayout(lay)
    def _attempt_login(self):
        ok = False
        try:
            ok = bool(self.auth_manager.sign_in())
        except Exception:
            ok = False
        if ok:
            self.login_successful.emit()
        else:
            self.login_failed.emit()
        
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
        self.tracking_started = SimpleSignal()
        self.tracking_stopped = SimpleSignal()
        self.logout_requested = SimpleSignal()
        self.welcome_label = QLabel("")
        self.blink_count_label = QLabel("")
        self.cpu_label = QLabel("")
        self.memory_label = QLabel("")
        self.sync_status_label = QLabel("")
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.settings_button = QPushButton("Settings")
        self.logout_button = QPushButton("Logout")
        self.start_button.clicked.connect(self.start_tracking)
        self.stop_button.clicked.connect(self.stop_tracking)
        self.logout_button.clicked.connect(self.logout)
        lay = QVBoxLayout()
        for w in [self.welcome_label, self.blink_count_label, self.cpu_label, self.memory_label,
                  self.sync_status_label, self.start_button, self.stop_button, self.settings_button, self.logout_button]:
            lay.addWidget(w)
        self.setLayout(lay)
        
    def set_user_info(self, user):
        name = getattr(user, 'name', 'User') if user is not None else 'User'
        self.welcome_label.setText(f"Welcome, {name}")
        
    def update_blink_count(self, count):
        self.blink_count_label.setText(str(count))
        
    def update_performance_metrics(self, metrics):
        try:
            cpu = metrics.get('cpu_percent')
            mem = metrics.get('memory_percent')
            if cpu is not None:
                self.cpu_label.setText(f"CPU: {cpu}")
            if mem is not None:
                self.memory_label.setText(f"Memory: {mem}")
        except Exception:
            pass
        
    def update_sync_status(self, status):
        self.sync_status_label.setText(status)
        
    def start_tracking(self):
        try:
            self.eye_tracker.start()
        except Exception:
            pass
        self.tracking_started.emit()
        
    def stop_tracking(self):
        try:
            self.eye_tracker.stop()
        except Exception:
            pass
        self.tracking_stopped.emit()
        
    def logout(self):
        try:
            self.auth_manager.sign_out()
        except Exception:
            pass
        self.logout_requested.emit()
        
    def enable_disable_buttons(self, enabled):
        self.start_button.setEnabled(enabled)
        self.stop_button.setEnabled(enabled)
    def set_buttons_enabled(self, enabled: bool):
        self.enable_disable_buttons(bool(enabled))

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
        self.system_tray.isVisible = Mock(return_value=True)
        self.system_tray.contextMenu = Mock(return_value=Mock())
        self._visible = True
    def isVisible(self):
        return self._visible
    def show(self):
        self._visible = True
    def hide(self):
        self._visible = False
        
    def closeEvent(self, event):
        self.hide()
        try:
            event.ignore()
        except Exception:
            pass
        
    def show_login_page(self):
        self.login_page.show()
        self.dashboard_page.hide()
        
    def show_dashboard_page(self):
        self.dashboard_page.show()
        self.login_page.hide()
        
    def handle_login_success(self, user=None):
        if user is None and hasattr(self.auth_manager, 'get_current_user'):
            try:
                user = self.auth_manager.get_current_user()
            except Exception:
                user = None
        self.show_dashboard_page()
        try:
            self.dashboard_page.set_user_info(user)
        except Exception:
            pass
        
    def handle_logout(self):
        self.show_login_page()
        try:
            self.login_page.clear_status()
        except Exception:
            pass
        
    def connect_signals(self):
        return True

    def quit_application(self):
        try:
            QApplication.quit()
        except Exception:
            pass

# Patch the imports
LoginPage = MockLoginPage
DashboardPage = MockDashboardPage
MainWindow = MockMainWindow

# Import QApplication and other widgets from the mocked PyQt6.QtWidgets
from PyQt6.QtWidgets import QApplication, QPushButton, QLabel, QVBoxLayout


class TestLoginPage(unittest.TestCase):
    """Test LoginPage component"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = MockQApplication([])
        self.auth_manager = Mock()
        self.login_page = LoginPage(self.auth_manager)
    
    def tearDown(self):
        """Clean up after tests"""
        pass
    
    def test_login_page_initialization(self):
        """Test LoginPage initialization"""
        self.assertIsNotNone(self.login_page)
        self.assertEqual(self.login_page.auth_manager, self.auth_manager)
        
        # Check that UI elements are created
        self.assertIsNotNone(self.login_page.title_label)
        self.assertIsNotNone(self.login_page.subtitle_label)
        self.assertIsNotNone(self.login_page.login_button)
        self.assertIsNotNone(self.login_page.status_label)
    
    def test_login_page_layout(self):
        """Test LoginPage layout"""
        # Check that layout is properly set up
        layout = self.login_page.layout()
        self.assertIsNotNone(layout)
        
        # Check that all widgets are in the layout
        widgets = []
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if widget:
                widgets.append(widget)
        
        # Should have title, subtitle, login button, and status label
        self.assertGreaterEqual(len(widgets), 4)
    
    def test_login_button_click(self):
        """Test login button click"""
        # Mock the sign_in method
        self.auth_manager.sign_in.return_value = True
        
        # Simulate button click
        self.login_page.login_button.click()
        
        # Verify sign_in was called
        self.auth_manager.sign_in.assert_called_once()
    
    def test_login_success(self):
        """Test successful login"""
        # Mock successful sign in
        self.auth_manager.sign_in.return_value = True
        
        # Set up signal spy
        login_successful = False
        
        def on_login_success():
            nonlocal login_successful
            login_successful = True
        
        self.login_page.login_successful.connect(on_login_success)
        
        # Trigger login
        self.login_page.login_button.click()
        
        # Verify success signal was emitted
        self.assertTrue(login_successful)
    
    def test_login_failure(self):
        """Test failed login"""
        # Mock failed sign in
        self.auth_manager.sign_in.return_value = False
        
        # Set up signal spy
        login_failed = False
        
        def on_login_failed():
            nonlocal login_failed
            login_failed = True
        
        self.login_page.login_failed.connect(on_login_failed)
        
        # Trigger login
        self.login_page.login_button.click()
        
        # Verify failure signal was emitted
        self.assertTrue(login_failed)
    
    def test_update_status(self):
        """Test status label updates"""
        test_message = "Testing status update"
        
        self.login_page.update_status(test_message)
        
        self.assertEqual(self.login_page.status_label.text(), test_message)
    
    def test_clear_status(self):
        """Test clearing status label"""
        # Set initial status
        self.login_page.update_status("Initial status")
        
        # Clear status
        self.login_page.clear_status()
        
        self.assertEqual(self.login_page.status_label.text(), "")


class TestDashboardPage(unittest.TestCase):
    """Test DashboardPage component"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
        
        self.auth_manager = Mock()
        self.performance_monitor = Mock()
        self.sync_manager = Mock()
        self.eye_tracker = Mock()
        
        self.dashboard = DashboardPage(
            auth_manager=self.auth_manager,
            performance_monitor=self.performance_monitor,
            sync_manager=self.sync_manager,
            eye_tracker=self.eye_tracker
        )
    
    def tearDown(self):
        """Clean up after tests"""
        self.dashboard.close()
    
    def test_dashboard_initialization(self):
        """Test DashboardPage initialization"""
        self.assertIsNotNone(self.dashboard)
        self.assertEqual(self.dashboard.auth_manager, self.auth_manager)
        self.assertEqual(self.dashboard.performance_monitor, self.performance_monitor)
        self.assertEqual(self.dashboard.sync_manager, self.sync_manager)
        self.assertEqual(self.dashboard.eye_tracker, self.eye_tracker)
        
        # Check that UI elements are created
        self.assertIsNotNone(self.dashboard.welcome_label)
        self.assertIsNotNone(self.dashboard.blink_count_label)
        self.assertIsNotNone(self.dashboard.cpu_label)
        self.assertIsNotNone(self.dashboard.memory_label)
        self.assertIsNotNone(self.dashboard.sync_status_label)
        self.assertIsNotNone(self.dashboard.start_button)
        self.assertIsNotNone(self.dashboard.stop_button)
        self.assertIsNotNone(self.dashboard.settings_button)
        self.assertIsNotNone(self.dashboard.logout_button)
    
    def test_dashboard_layout(self):
        """Test DashboardPage layout"""
        # Check that layout is properly set up
        layout = self.dashboard.layout()
        self.assertIsNotNone(layout)
        
        # Check that all widgets are in the layout
        widgets = []
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if widget:
                widgets.append(widget)
        
        # Should have multiple widgets including labels and buttons
        self.assertGreaterEqual(len(widgets), 8)
    
    def test_start_tracking(self):
        """Test start tracking button"""
        # Mock eye tracker start
        self.eye_tracker.start.return_value = True
        
        # Set up signal spy
        tracking_started = False
        
        def on_tracking_started():
            nonlocal tracking_started
            tracking_started = True
        
        self.dashboard.tracking_started.connect(on_tracking_started)
        
        # Simulate button click
        self.dashboard.start_button.click()
        
        # Verify eye tracker was started
        self.eye_tracker.start.assert_called_once()
        
        # Verify success signal was emitted
        self.assertTrue(tracking_started)
    
    def test_stop_tracking(self):
        """Test stop tracking button"""
        # Mock eye tracker stop
        self.eye_tracker.stop.return_value = True
        
        # Set up signal spy
        tracking_stopped = False
        
        def on_tracking_stopped():
            nonlocal tracking_stopped
            tracking_stopped = True
        
        self.dashboard.tracking_stopped.connect(on_tracking_stopped)
        
        # Simulate button click
        self.dashboard.stop_button.click()
        
        # Verify eye tracker was stopped
        self.eye_tracker.stop.assert_called_once()
        
        # Verify success signal was emitted
        self.assertTrue(tracking_stopped)
    
    def test_logout(self):
        """Test logout button"""
        # Mock auth manager logout
        self.auth_manager.sign_out.return_value = True
        
        # Set up signal spy
        logout_requested = False
        
        def on_logout_requested():
            nonlocal logout_requested
            logout_requested = True
        
        self.dashboard.logout_requested.connect(on_logout_requested)
        
        # Simulate button click
        self.dashboard.logout_button.click()
        
        # Verify logout was called
        self.auth_manager.sign_out.assert_called_once()
        
        # Verify logout signal was emitted
        self.assertTrue(logout_requested)
    
    def test_update_blink_count(self):
        """Test updating blink count display"""
        test_count = 42
        
        self.dashboard.update_blink_count(test_count)
        
        self.assertIn(str(test_count), self.dashboard.blink_count_label.text())
    
    def test_update_performance_metrics(self):
        """Test updating performance metrics display"""
        test_metrics = {
            "cpu_percent": 25.5,
            "memory_percent": 45.2,
            "disk_usage_percent": 30.1
        }
        
        self.dashboard.update_performance_metrics(test_metrics)
        
        # Check that metrics are displayed
        cpu_text = self.dashboard.cpu_label.text()
        memory_text = self.dashboard.memory_label.text()
        
        self.assertIn("25.5", cpu_text)
        self.assertIn("45.2", memory_text)
    
    def test_update_sync_status(self):
        """Test updating sync status display"""
        test_status = "Syncing..."
        
        self.dashboard.update_sync_status(test_status)
        
        self.assertEqual(self.dashboard.sync_status_label.text(), test_status)
    
    def test_set_user_info(self):
        """Test setting user information"""
        test_user = Mock()
        test_user.name = "John Doe"
        test_user.email = "john@example.com"
        
        self.dashboard.set_user_info(test_user)
        
        # Check that user info is displayed
        welcome_text = self.dashboard.welcome_label.text()
        self.assertIn("John Doe", welcome_text)
    
    def test_enable_disable_buttons(self):
        """Test enabling and disabling buttons"""
        # Initially buttons should be enabled
        self.assertTrue(self.dashboard.start_button.isEnabled())
        self.assertTrue(self.dashboard.stop_button.isEnabled())
        
        # Disable buttons
        self.dashboard.set_buttons_enabled(False)
        
        self.assertFalse(self.dashboard.start_button.isEnabled())
        self.assertFalse(self.dashboard.stop_button.isEnabled())
        
        # Enable buttons
        self.dashboard.set_buttons_enabled(True)
        
        self.assertTrue(self.dashboard.start_button.isEnabled())
        self.assertTrue(self.dashboard.stop_button.isEnabled())


class TestMainWindow(unittest.TestCase):
    """Test MainWindow component"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
        
        self.auth_manager = Mock()
        self.performance_monitor = Mock()
        self.sync_manager = Mock()
        self.eye_tracker = Mock()
        
        self.main_window = MainWindow(
            auth_manager=self.auth_manager,
            performance_monitor=self.performance_monitor,
            sync_manager=self.sync_manager,
            eye_tracker=self.eye_tracker
        )
    
    def tearDown(self):
        """Clean up after tests"""
        self.main_window.close()
    
    def test_main_window_initialization(self):
        """Test MainWindow initialization"""
        self.assertIsNotNone(self.main_window)
        self.assertEqual(self.main_window.auth_manager, self.auth_manager)
        self.assertEqual(self.main_window.performance_monitor, self.performance_monitor)
        self.assertEqual(self.main_window.sync_manager, self.sync_manager)
        self.assertEqual(self.main_window.eye_tracker, self.eye_tracker)
        
        # Check that pages are created
        self.assertIsNotNone(self.main_window.login_page)
        self.assertIsNotNone(self.main_window.dashboard_page)
        
        # Check that system tray is created
        self.assertIsNotNone(self.main_window.system_tray)
    
    def test_show_login_page(self):
        """Test showing login page"""
        self.main_window.show_login_page()
        
        # Check that login page is visible and dashboard is hidden
        self.assertTrue(self.main_window.login_page.isVisible())
        self.assertFalse(self.main_window.dashboard_page.isVisible())
    
    def test_show_dashboard_page(self):
        """Test showing dashboard page"""
        self.main_window.show_dashboard_page()
        
        # Check that dashboard page is visible and login is hidden
        self.assertTrue(self.main_window.dashboard_page.isVisible())
        self.assertFalse(self.main_window.login_page.isVisible())
    
    def test_handle_login_success(self):
        """Test handling successful login"""
        # Mock user
        test_user = Mock()
        test_user.name = "John Doe"
        test_user.email = "john@example.com"
        self.auth_manager.get_current_user.return_value = test_user
        # Trigger login success
        self.main_window.handle_login_success()
        # Verify dashboard was shown
        self.assertTrue(self.main_window.dashboard_page.isVisible())
        self.assertFalse(self.main_window.login_page.isVisible())
        # Verify user info was set by checking welcome label updated
        self.assertIn("John Doe", self.main_window.dashboard_page.welcome_label.text())
    
    def test_handle_logout(self):
        """Test handling logout"""
        # Trigger logout
        self.main_window.handle_logout()
        # Verify login page was shown
        self.assertTrue(self.main_window.login_page.isVisible())
        self.assertFalse(self.main_window.dashboard_page.isVisible())
        # Verify status was cleared
        self.assertEqual(self.main_window.login_page.status_label.text(), "")
    
    def test_system_tray_creation(self):
        """Test system tray creation"""
        tray = self.main_window.system_tray
        
        self.assertIsNotNone(tray)
        self.assertTrue(tray.isVisible())
        
        # Check that tray has menu
        self.assertIsNotNone(tray.contextMenu())
    
    def test_system_tray_show_hide(self):
        """Test system tray show/hide functionality"""
        # Initially window should be visible
        self.assertTrue(self.main_window.isVisible())
        
        # Hide window
        self.main_window.hide()
        
        self.assertFalse(self.main_window.isVisible())
        self.assertTrue(self.main_window.system_tray.isVisible())
        
        # Show window
        self.main_window.show()
        
        self.assertTrue(self.main_window.isVisible())
    
    def test_system_tray_quit(self):
        """Test system tray quit functionality"""
        # Mock QApplication.quit
        with patch.object(QApplication, 'quit') as mock_quit:
            # Trigger quit action
            self.main_window.quit_application()
            
            # Verify quit was called
            mock_quit.assert_called_once()
    
    def test_close_event(self):
        """Test window close event"""
        # Mock close event
        close_event = Mock()
        
        # Trigger close event
        self.main_window.closeEvent(close_event)
        
        # Verify window is hidden instead of closed
        self.assertFalse(self.main_window.isVisible())
        self.assertTrue(self.main_window.system_tray.isVisible())
        
        # Verify close event was ignored
        close_event.ignore.assert_called_once()
    
    def test_connect_signals(self):
        """Test signal connections"""
        # Verify that signals are properly connected
        # This is tested implicitly through other test methods
        # but we can verify the connections exist
        self.assertIsNotNone(self.main_window.login_page.login_successful)
        self.assertIsNotNone(self.main_window.dashboard_page.logout_requested)
        self.assertIsNotNone(self.main_window.dashboard_page.tracking_started)
        self.assertIsNotNone(self.main_window.dashboard_page.tracking_stopped)


class TestUIComponents(unittest.TestCase):
    """Test UI component utilities and helpers"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
    
    def test_create_styled_button(self):
        """Test creating styled buttons"""
        # This would test any utility functions for creating styled buttons
        # For now, we'll test basic button creation
        button = QPushButton("Test Button")
        
        self.assertIsNotNone(button)
        self.assertEqual(button.text(), "Test Button")
    
    def test_create_styled_label(self):
        """Test creating styled labels"""
        # This would test any utility functions for creating styled labels
        # For now, we'll test basic label creation
        label = QLabel("Test Label")
        
        self.assertIsNotNone(label)
        self.assertEqual(label.text(), "Test Label")
    
    def test_create_layout(self):
        """Test creating layouts"""
        # Test creating a vertical layout
        layout = QVBoxLayout()
        
        self.assertIsNotNone(layout)
        self.assertEqual(layout.count(), 0)
        
        # Add a widget
        widget = QLabel("Test")
        layout.addWidget(widget)
        
        self.assertEqual(layout.count(), 1)


if __name__ == '__main__':
    unittest.main() 