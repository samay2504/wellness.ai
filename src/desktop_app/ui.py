"""
User Interface module for Wellness at Work
Modern PyQt6-based interface with system tray integration
"""

import sys
import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QStackedWidget, QSystemTrayIcon,
    QMenu, QProgressBar, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QAction, QIcon, QFont, QPalette, QColor
from .themes.theme import apply_theme

from .auth import AuthManager, User
from .metrics import PerformanceMonitor
from .sync import SyncManager
from .eye_tracker_ui import EyeTrackerUI

logger = logging.getLogger(__name__)


class LoginPage(QWidget):
    """Login page with Google OAuth"""
    
    login_successful = pyqtSignal(User)
    
    def __init__(self, auth_manager: AuthManager):
        super().__init__()
        self.auth_manager = auth_manager
        self.init_ui()
    
    def init_ui(self):
        """Initialize login UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Wellness at Work")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 20px;")
        
        # Subtitle
        subtitle = QLabel("Eye Tracking for Better Health")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d; margin: 10px;")
        
        # Login button
        self.login_btn = QPushButton("Sign in with Google")
        self.login_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3367d6;
            }
            QPushButton:pressed {
                background-color: #2a56c6;
            }
        """)
        self.login_btn.clicked.connect(self.handle_login)
        
        # Email signup button
        self.signup_btn = QPushButton("Sign up with Email")
        self.signup_btn.setFont(QFont("Arial", 12))
        self.signup_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        self.signup_btn.clicked.connect(self.handle_signup)
        
        # Email login button
        self.email_login_btn = QPushButton("Sign in with Email")
        self.email_login_btn.setFont(QFont("Arial", 12))
        self.email_login_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
            QPushButton:pressed {
                background-color: #1b2631;
            }
        """)
        self.email_login_btn.clicked.connect(self.handle_email_login)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #e74c3c; margin: 10px;")
        
        # Layout
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()
        layout.addWidget(self.login_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.email_login_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.signup_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def handle_login(self):
        """Handle login button click"""
        self.login_btn.setEnabled(False)
        self.status_label.setText("Signing in...")
        self.status_label.setStyleSheet("color: #3498db; margin: 10px;")
        
        # Run authentication in separate thread
        self.auth_thread = AuthThread(self.auth_manager)
        self.auth_thread.auth_complete.connect(self.on_auth_complete)
        self.auth_thread.start()
    
    def handle_signup(self):
        """Handle signup button click"""
        from .email_auth_dialog import EmailAuthDialog
        from PyQt6.QtWidgets import QDialog
        dialog = EmailAuthDialog(self, mode='signup')
        if dialog.exec() == QDialog.DialogCode.Accepted:
            email, password, name = dialog.get_credentials()
            self.register_user(email, password, name)
    
    def handle_email_login(self):
        """Handle email login button click"""
        from .email_auth_dialog import EmailAuthDialog
        from PyQt6.QtWidgets import QDialog
        dialog = EmailAuthDialog(self, mode='login')
        if dialog.exec() == QDialog.DialogCode.Accepted:
            email, password, _ = dialog.get_credentials()
            self.login_user(email, password)
    
    def register_user(self, email, password, name):
        """Register new user with enhanced auth service"""
        try:
            from desktop_app.auth_service import AuthService
            auth_service = AuthService()
            
            result = auth_service.register_user(email, password, name)
            
            if result["success"]:
                user = User(
                    id=result['user']['id'], 
                    name=result['user']['name'], 
                    email=result['user']['email'], 
                    consent=True
                )
                self.login_successful.emit(user)
            else:
                self.status_label.setText(f"Registration failed: {result.get('error', 'Unknown error')}")
                self.status_label.setStyleSheet("color: #e74c3c; margin: 10px;")
                
        except ImportError:
            # Fallback to simple registration
            self._fallback_register(email, password, name)
        except Exception as e:
            logger.error(f"Registration error: {e}")
            self.status_label.setText("Registration failed. Please try again.")
            self.status_label.setStyleSheet("color: #e74c3c; margin: 10px;")
    
    def _fallback_register(self, email, password, name):
        """Fallback registration without Redis"""
        import secrets
        user = User(
            id=secrets.token_urlsafe(16),
            name=name,
            email=email,
            consent=True
        )
        self.login_successful.emit(user)
    
    def login_user(self, email, password):
        """Login user with enhanced auth service"""
        try:
            from desktop_app.auth_service import AuthService
            auth_service = AuthService()
            
            result = auth_service.login_user(email, password)
            
            if result["success"]:
                user = User(
                    id=result['user']['id'], 
                    name=result['user']['name'], 
                    email=result['user']['email'], 
                    consent=True
                )
                self.login_successful.emit(user)
            else:
                self.status_label.setText(f"Login failed: {result.get('error', 'Invalid credentials')}")
                self.status_label.setStyleSheet("color: #e74c3c; margin: 10px;")
                
        except ImportError:
            # Fallback to simple login
            self._fallback_login(email, password)
        except Exception as e:
            logger.error(f"Login error: {e}")
            self.status_label.setText("Login failed. Please try again.")
            self.status_label.setStyleSheet("color: #e74c3c; margin: 10px;")
    
    def _fallback_login(self, email, password):
        """Fallback login without Redis"""
        import secrets
        user = User(
            id=secrets.token_urlsafe(16),
            name=email.split('@')[0],
            email=email,
            consent=True
        )
        self.login_successful.emit(user)
    
    def on_auth_complete(self, user: Optional[User]):
        """Handle authentication completion"""
        if user:
            self.login_successful.emit(user)
        else:
            self.status_label.setText("Authentication failed. Please try again.")
            self.status_label.setStyleSheet("color: #e74c3c; margin: 10px;")
            self.login_btn.setEnabled(True)


class AuthThread(QThread):
    """Thread for handling authentication"""
    auth_complete = pyqtSignal(object)
    
    def __init__(self, auth_manager: AuthManager):
        super().__init__()
        self.auth_manager = auth_manager
    
    def run(self):
        """Run authentication"""
        user = self.auth_manager.sign_in()
        self.auth_complete.emit(user)


class DashboardPage(QWidget):
    """Main dashboard with eye tracking and performance metrics"""
    
    def __init__(self, auth_manager: AuthManager, performance_monitor: PerformanceMonitor,
                 sync_manager: SyncManager, eye_tracker: EyeTrackerUI, eye_blink_tracker=None,
                 data_storage=None):
        super().__init__()
        self.auth_manager = auth_manager
        self.performance_monitor = performance_monitor
        self.sync_manager = sync_manager
        self.eye_tracker = eye_tracker
        self.eye_blink_tracker = eye_blink_tracker
        self.data_storage = data_storage
        self.init_ui()
        self.setup_timers()
        
        # Set up blink callback if tracker available
        if self.eye_blink_tracker:
            self.eye_blink_tracker.add_blink_callback(self.on_blink_detected)
    
    def init_ui(self):
        """Initialize dashboard UI"""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        # User info
        self.user_label = QLabel("Welcome!")
        self.user_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.user_label.setStyleSheet("color: #2c3e50;")
        
        # Sign out button
        self.signout_btn = QPushButton("Sign Out")
        self.signout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.signout_btn.clicked.connect(self.handle_signout)
        
        header_layout.addWidget(self.user_label)
        header_layout.addStretch()
        header_layout.addWidget(self.signout_btn)
        
        # Main content
        content_layout = QGridLayout()
        
        # Eye tracking section
        tracking_frame = QFrame()
        tracking_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        tracking_frame.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 8px; padding: 15px; }")
        
        tracking_layout = QVBoxLayout()
        
        tracking_title = QLabel("Eye Tracking")
        tracking_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        tracking_title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        
        self.blink_count_label = QLabel("Blink Count: 0")
        self.blink_count_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.blink_count_label.setStyleSheet("color: #27ae60;")
        
        self.tracking_status_label = QLabel("Status: Stopped")
        self.tracking_status_label.setStyleSheet("color: #7f8c8d;")
        
        self.start_tracking_btn = QPushButton("Start Tracking")
        self.start_tracking_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.start_tracking_btn.clicked.connect(self.toggle_tracking)
        
        tracking_layout.addWidget(tracking_title)
        tracking_layout.addWidget(self.blink_count_label)
        tracking_layout.addWidget(self.tracking_status_label)
        tracking_layout.addWidget(self.start_tracking_btn)
        tracking_frame.setLayout(tracking_layout)
        
        # Performance metrics section
        perf_frame = QFrame()
        perf_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        perf_frame.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 8px; padding: 15px; }")
        
        perf_layout = QVBoxLayout()
        
        perf_title = QLabel("System Performance")
        perf_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        perf_title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        
        # CPU Usage
        cpu_layout = QHBoxLayout()
        cpu_label = QLabel("CPU:")
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setMaximum(100)
        self.cpu_value_label = QLabel("0%")
        cpu_layout.addWidget(cpu_label)
        cpu_layout.addWidget(self.cpu_progress)
        cpu_layout.addWidget(self.cpu_value_label)
        
        # Memory Usage
        mem_layout = QHBoxLayout()
        mem_label = QLabel("Memory:")
        self.mem_progress = QProgressBar()
        self.mem_progress.setMaximum(100)
        self.mem_value_label = QLabel("0 MB")
        mem_layout.addWidget(mem_label)
        mem_layout.addWidget(self.mem_progress)
        mem_layout.addWidget(self.mem_value_label)
        
        # Energy Impact
        energy_layout = QHBoxLayout()
        energy_label = QLabel("Energy:")
        self.energy_progress = QProgressBar()
        self.energy_progress.setMaximum(100)
        self.energy_value_label = QLabel("Low")
        energy_layout.addWidget(energy_label)
        energy_layout.addWidget(self.energy_progress)
        energy_layout.addWidget(self.energy_value_label)
        
        perf_layout.addWidget(perf_title)
        perf_layout.addLayout(cpu_layout)
        perf_layout.addLayout(mem_layout)
        perf_layout.addLayout(energy_layout)
        perf_frame.setLayout(perf_layout)
        
        # Sync status
        sync_frame = QFrame()
        sync_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        sync_frame.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 8px; padding: 15px; }")
        
        sync_layout = QVBoxLayout()
        
        sync_title = QLabel("Data Sync")
        sync_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        sync_title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        
        self.sync_status_label = QLabel("Status: Disconnected")
        self.sync_status_label.setStyleSheet("color: #7f8c8d;")
        
        sync_layout.addWidget(sync_title)
        sync_layout.addWidget(self.sync_status_label)
        sync_frame.setLayout(sync_layout)
        
        # Add frames to grid
        content_layout.addWidget(tracking_frame, 0, 0)
        content_layout.addWidget(perf_frame, 0, 1)
        content_layout.addWidget(sync_frame, 1, 0, 1, 2)
        
        # Main layout
        layout.addLayout(header_layout)
        layout.addLayout(content_layout)
        
        self.setLayout(layout)
    
    def setup_timers(self):
        """Setup update timers"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(1000)  # Update every second
        # Connect eye tracker signals
        self.eye_tracker.blink_count_updated.connect(self.update_blink_count)
        self.eye_tracker.status_updated.connect(self.update_tracking_status)
    
    def on_blink_detected(self, blink_data, additional_data=None):
        """Handle blink detection from new blink tracker"""
        self.blink_count_label.setText(f"Blink Count: {blink_data.blink_count}")
        
    def update_blink_count(self, count):
        """Update blink count display"""
        self.blink_count_label.setText(f"Blink Count: {count}")
        
    def update_tracking_status(self, status):
        """Update tracking status display"""
        self.tracking_status_label.setText(f"Status: {status}")

    def update_metrics(self):
        """Update performance metrics"""
        # Update user info
        user = self.auth_manager.get_current_user()
        if user:
            self.user_label.setText(f"Welcome, {user.name}!")
        
        # Update performance metrics
        current_metrics = self.performance_monitor.get_current_metrics()
        if current_metrics:
            self.cpu_progress.setValue(int(current_metrics.cpu_percent))
            self.cpu_value_label.setText(f"{current_metrics.cpu_percent:.1f}%")
            
            mem_mb = current_metrics.memory_mb
            mem_percent = current_metrics.memory_percent
            self.mem_progress.setValue(int(mem_percent))
            self.mem_value_label.setText(f"{mem_mb:.0f} MB")
            
            # Handle battery/energy display
            if hasattr(current_metrics, 'battery_percent') and current_metrics.battery_percent is not None:
                self.energy_value_label.setText(f"{current_metrics.battery_percent:.1f}%")
            else:
                self.energy_value_label.setText("N/A")
        
        # Update sync status
        sync_status = self.sync_manager.get_status()
        self.sync_status_label.setText(f"Status: {sync_status}")

    def update_tracking_status(self, status):
        """Update tracking status display"""
        self.tracking_status_label.setText(f"Status: {status}")
        if status == "Running":
            self.start_tracking_btn.setText("Stop Tracking")
            self.start_tracking_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
        else:
            self.start_tracking_btn.setText("Start Tracking")
            self.start_tracking_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
            """)

    def toggle_tracking(self):
        """Toggle eye tracking on/off"""
        if hasattr(self, 'eye_blink_tracker') and self.eye_blink_tracker:
            if self.eye_blink_tracker.is_running:
                self.eye_blink_tracker.stop_tracking()
                self.start_tracking_btn.setText("Start Tracking")
                self.tracking_status_label.setText("Status: Stopped")
            else:
                self.eye_blink_tracker.start_tracking()
                self.start_tracking_btn.setText("Stop Tracking")
                self.tracking_status_label.setText("Status: Active")
        else:
            # Fallback to old eye tracker if blink tracker not available
            if self.eye_tracker.is_running():
                self.eye_tracker.stop_tracking()
            else:
                self.eye_tracker.start_tracking()
    
    def handle_signout(self):
        """Handle sign out"""
        self.auth_manager.sign_out()
        # Emit signal to return to login page
        self.parent().parent().show_login_page()


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, auth_manager: AuthManager, performance_monitor: PerformanceMonitor,
                 sync_manager: SyncManager, eye_tracker: EyeTrackerUI, eye_blink_tracker=None,
                 data_storage=None):
        super().__init__()
        self.auth_manager = auth_manager
        self.performance_monitor = performance_monitor
        self.sync_manager = sync_manager
        self.eye_tracker = eye_tracker
        self.eye_blink_tracker = eye_blink_tracker
        self.data_storage = data_storage
        
        self.init_ui()
        self.setup_system_tray()
        self.show_login_page()
    
    def init_ui(self):
        """Initialize main window UI"""
        self.setWindowTitle("Wellness at Work")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(600, 400)
        # Apply lightweight modern theme
        apply_theme(self)
        
        # Create stacked widget for pages
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create pages
        self.login_page = LoginPage(self.auth_manager)
        self.dashboard_page = DashboardPage(
            self.auth_manager, self.performance_monitor,
            self.sync_manager, self.eye_tracker, self.eye_blink_tracker,
            self.data_storage
        )
        
        # Connect signals
        self.login_page.login_successful.connect(self.show_dashboard)
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.dashboard_page)
    
    def setup_system_tray(self):
        """Setup system tray icon and menu"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("assets/icon.png"))  # You'll need to add an icon
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show/Hide", self)
        show_action.triggered.connect(self.toggle_window)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Connect double-click to show window
        self.tray_icon.activated.connect(self.tray_icon_activated)
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_window()
    
    def toggle_window(self):
        """Toggle window visibility"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def show_login_page(self):
        """Show login page"""
        self.stacked_widget.setCurrentWidget(self.login_page)
        self.setWindowTitle("Wellness at Work - Sign In")
    
    def show_dashboard(self, user: User):
        """Show dashboard page"""
        self.stacked_widget.setCurrentWidget(self.dashboard_page)
        self.setWindowTitle(f"Wellness at Work - {user.name}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Hide to tray instead of closing
        self.hide()
        event.ignore() 