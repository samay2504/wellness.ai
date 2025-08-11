"""
Modern Authentication UI with GDPR Compliance
Production-ready, minimal, and futuristic design
"""

import sys
import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QTabWidget, QWidget,
                            QMessageBox, QProgressBar, QTextEdit, QCheckBox,
                            QFrame, QScrollArea, QApplication)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor, QPainter, QLinearGradient

from desktop_app.auth import AuthManager, User
from desktop_app.email_auth import EmailAuthManager

logger = logging.getLogger(__name__)

class ModernCard(QFrame):
    """Modern card widget with shadow effect"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(200, 200, 200, 0.3);
                border-radius: 12px;
                padding: 20px;
            }
        """)
        self.setFrameStyle(QFrame.Shape.Box)

class ModernButton(QPushButton):
    """Modern button with hover effects"""
    
    def __init__(self, text, button_type="primary", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self.setFixedHeight(44)
        self.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_style()
    
    def apply_style(self):
        if self.button_type == "primary":
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                    color: white;
                    border: none;
                    border-radius: 22px;
                    font-weight: 600;
                    padding: 0 24px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #5a6fd8, stop:1 #6a4190);
                    transform: scale(1.02);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #4e5bc6, stop:1 #5e377e);
                }
                QPushButton:disabled {
                    background: #cccccc;
                    color: #666666;
                }
            """)
        elif self.button_type == "secondary":
            self.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #667eea;
                    border: 2px solid #667eea;
                    border-radius: 22px;
                    font-weight: 600;
                    padding: 0 24px;
                }
                QPushButton:hover {
                    background: rgba(102, 126, 234, 0.1);
                    border-color: #5a6fd8;
                }
                QPushButton:pressed {
                    background: rgba(102, 126, 234, 0.2);
                }
            """)
        elif self.button_type == "google":
            self.setStyleSheet("""
                QPushButton {
                    background: white;
                    color: #1f1f1f;
                    border: 1px solid #dadce0;
                    border-radius: 22px;
                    font-weight: 500;
                    padding: 0 24px;
                }
                QPushButton:hover {
                    background: #f8f9fa;
                    border-color: #c1c7cd;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
            """)

class ModernInput(QLineEdit):
    """Modern input field with floating label effect"""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(48)
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(200, 200, 200, 0.3);
                border-radius: 8px;
                padding: 0 16px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #667eea;
                background: white;
            }
            QLineEdit:hover {
                border-color: rgba(102, 126, 234, 0.5);
            }
        """)

class GDPRDialog(QDialog):
    """GDPR compliance and privacy notice dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Privacy & Data Protection")
        self.setFixedSize(600, 700)
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("🛡️ Your Privacy Matters")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #2c3e50; margin: 20px 0;")
        layout.addWidget(header)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # GDPR content
        gdpr_text = """
        <div style="font-family: 'Segoe UI'; font-size: 12px; line-height: 1.6; color: #34495e;">
        <h3 style="color: #2c3e50;">🔒 Data Protection & Privacy</h3>
        <p><strong>We are committed to protecting your privacy and complying with GDPR regulations.</strong></p>
        
        <h4>What data we collect:</h4>
        <ul>
        <li>Email address and name (for authentication)</li>
        <li>Eye tracking metrics (stored locally)</li>
        <li>Usage analytics (anonymized)</li>
        </ul>
        
        <h4>How we protect your data:</h4>
        <ul>
        <li>🔐 End-to-end encryption (AES-256)</li>
        <li>🏠 Local data storage priority</li>
        <li>🔑 Secure credential management</li>
        <li>📝 Comprehensive audit logging</li>
        </ul>
        
        <h4>Your rights under GDPR:</h4>
        <ul>
        <li>✅ <strong>Access:</strong> View all your data</li>
        <li>✏️ <strong>Rectification:</strong> Correct inaccurate data</li>
        <li>🗑️ <strong>Erasure:</strong> Delete your data</li>
        <li>📦 <strong>Portability:</strong> Export your data</li>
        <li>⛔ <strong>Restriction:</strong> Limit data processing</li>
        </ul>
        
        <h4>Legal basis for processing:</h4>
        <p>We process your data based on:</p>
        <ul>
        <li>📄 <strong>Consent:</strong> For optional features</li>
        <li>📋 <strong>Contract:</strong> For service delivery</li>
        <li>⚖️ <strong>Legitimate Interest:</strong> For security and improvement</li>
        </ul>
        
        <p style="margin-top: 20px;"><em>You can withdraw consent or exercise your rights at any time through the Privacy Settings.</em></p>
        </div>
        """
        
        gdpr_label = QLabel(gdpr_text)
        gdpr_label.setWordWrap(True)
        scroll_layout.addWidget(gdpr_label)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Consent checkboxes
        consent_frame = ModernCard()
        consent_layout = QVBoxLayout(consent_frame)
        
        self.essential_consent = QCheckBox("I consent to essential data processing (required for app functionality)")
        self.essential_consent.setChecked(True)
        self.essential_consent.setEnabled(False)
        self.essential_consent.setStyleSheet("font-weight: bold; color: #2c3e50;")
        
        self.analytics_consent = QCheckBox("I consent to anonymized analytics to improve the service")
        self.analytics_consent.setChecked(True)
        
        self.marketing_consent = QCheckBox("I consent to receive updates about new features")
        
        consent_layout.addWidget(self.essential_consent)
        consent_layout.addWidget(self.analytics_consent)
        consent_layout.addWidget(self.marketing_consent)
        
        layout.addWidget(consent_frame)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        decline_btn = ModernButton("Decline", "secondary")
        decline_btn.clicked.connect(self.reject)
        
        accept_btn = ModernButton("Accept & Continue", "primary")
        accept_btn.clicked.connect(self.accept_privacy)
        
        button_layout.addWidget(decline_btn)
        button_layout.addWidget(accept_btn)
        layout.addWidget(button_layout)
        
        self.setLayout(layout)
    
    def accept_privacy(self):
        """Accept privacy terms and store consent"""
        try:
            from desktop_app.secure_storage import SecureDataManager
            storage = SecureDataManager()
            
            # Store consent preferences
            consent_data = {
                'essential': self.essential_consent.isChecked(),
                'analytics': self.analytics_consent.isChecked(),
                'marketing': self.marketing_consent.isChecked(),
                'timestamp': storage._get_timestamp(),
                'version': '1.0'
            }
            
            storage.store_consent(consent_data)
            storage.log_audit_event('consent_given', 'User accepted privacy terms')
            
        except Exception as e:
            logger.error(f"Failed to store consent: {e}")
        
        self.accept()

class AuthWorker(QThread):
    """Background worker for authentication operations"""
    
    # Signals
    oauth_success = pyqtSignal(object)  # User object
    oauth_error = pyqtSignal(str)       # Error message
    email_success = pyqtSignal(object)  # User object
    email_error = pyqtSignal(str)       # Error message
    
    def __init__(self, auth_type, **kwargs):
        super().__init__()
        self.auth_type = auth_type
        self.kwargs = kwargs
        
    def run(self):
        """Run authentication in background"""
        try:
            if self.auth_type == "oauth":
                self._oauth_auth()
            elif self.auth_type == "email_login":
                self._email_login()
            elif self.auth_type == "email_register":
                self._email_register()
            elif self.auth_type == "auto_login":
                self._auto_login()
                
        except Exception as e:
            logger.error(f"Auth worker error: {e}")
            if self.auth_type == "oauth":
                self.oauth_error.emit(str(e))
            else:
                self.email_error.emit(str(e))
    
    def _oauth_auth(self):
        """Handle OAuth authentication"""
        auth_manager = AuthManager()
        user = auth_manager.sign_in()
        if user:
            self.oauth_success.emit(user)
        else:
            self.oauth_error.emit("OAuth authentication failed")
    
    def _email_login(self):
        """Handle email login"""
        email_auth = EmailAuthManager()
        user = email_auth.login(
            self.kwargs['email'], 
            self.kwargs['password']
        )
        if user:
            self.email_success.emit(user)
        else:
            self.email_error.emit("Invalid email or password")
    
    def _email_register(self):
        """Handle email registration"""
        email_auth = EmailAuthManager()
        user = email_auth.register(
            self.kwargs['email'],
            self.kwargs['password'],
            self.kwargs['name']
        )
        if user:
            self.email_success.emit(user)
        else:
            self.email_error.emit("Registration failed. Email may already exist.")
    
    def _auto_login(self):
        """Handle auto login"""
        email_auth = EmailAuthManager()
        user = email_auth.auto_login()
        if user:
            self.email_success.emit(user)
        else:
            # Try OAuth auto-login as fallback
            auth_manager = AuthManager()
            if auth_manager.oauth_client:
                credentials = auth_manager.oauth_client.load_credentials()
                if credentials and auth_manager.oauth_client.refresh_credentials():
                    # Create user from stored credentials
                    try:
                        user_info = auth_manager._get_user_info(credentials)
                        if user_info:
                            user = User(
                                id=user_info.get('id', 'oauth_user'),
                                name=user_info.get('name', 'OAuth User'),
                                email=user_info.get('email', 'oauth@example.com'),
                                consent=True
                            )
                            auth_manager.current_user = user
                            self.oauth_success.emit(user)
                            return
                    except Exception as e:
                        logger.warning(f"Failed to get OAuth user info: {e}")
                        # Create fallback user from credentials
                        user = User(
                            id="oauth_user_stored",
                            name="OAuth User",
                            email="stored@oauth.com",
                            consent=True
                        )
                        self.oauth_success.emit(user)
                        return
            
            self.email_error.emit("No valid stored credentials found")

class AuthDialog(QDialog):
    """Modern authentication dialog with GDPR compliance"""
    
    def __init__(self, parent=None, skip_auto_login=False):
        super().__init__(parent)
        self.user = None
        self.auth_worker = None
        self.skip_auto_login = skip_auto_login
        self.setup_modern_ui()
        self.setup_connections()
        
        # Try auto-login first unless skipped
        if not skip_auto_login:
            self.try_auto_login()
        else:
            self.status_label.setText("Please sign in")
    
    def setup_modern_ui(self):
        """Setup modern UI with gradient background"""
        self.setWindowTitle("WellnessAI - Authentication")
        self.setFixedSize(480, 720)
        self.setModal(True)
        
        # Modern gradient background
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f7fafc, stop:0.5 #edf2f7, stop:1 #e2e8f0);
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(32, 32, 32, 32)
        
        # Header section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        # Logo/Icon
        logo_label = QLabel("🧠")
        logo_label.setFont(QFont("Segoe UI Emoji", 48))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(logo_label)
        
        # Title
        title_label = QLabel("WellnessAI")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2d3748; margin-bottom: 8px;")
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Your intelligent wellness companion")
        subtitle_label.setFont(QFont("Segoe UI", 12))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #718096; margin-bottom: 24px;")
        header_layout.addWidget(subtitle_label)
        
        main_layout.addLayout(header_layout)
        
        # Main content card
        content_card = ModernCard()
        content_layout = QVBoxLayout(content_card)
        content_layout.setSpacing(20)
        
        # Tab widget for different auth methods
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: rgba(255, 255, 255, 0.7);
                color: #4a5568;
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background: white;
                color: #2d3748;
                font-weight: 600;
            }
            QTabBar::tab:hover {
                background: rgba(255, 255, 255, 0.9);
            }
        """)
        
        # OAuth tab
        oauth_tab = QWidget()
        oauth_layout = QVBoxLayout(oauth_tab)
        oauth_layout.setSpacing(16)
        
        oauth_info = QLabel("Sign in with your Google account for seamless access")
        oauth_info.setFont(QFont("Segoe UI", 10))
        oauth_info.setStyleSheet("color: #718096; text-align: center;")
        oauth_info.setWordWrap(True)
        oauth_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        oauth_layout.addWidget(oauth_info)
        
        self.google_btn = ModernButton("🚀 Continue with Google", "google")
        oauth_layout.addWidget(self.google_btn)
        
        oauth_layout.addStretch()
        
        # Email tab
        email_tab = QWidget()
        email_layout = QVBoxLayout(email_tab)
        email_layout.setSpacing(16)
        
        # Login form
        login_group = QWidget()
        login_layout = QVBoxLayout(login_group)
        
        login_title = QLabel("Sign In")
        login_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        login_title.setStyleSheet("color: #2d3748; margin-bottom: 8px;")
        login_layout.addWidget(login_title)
        
        self.email_input = ModernInput("Email address")
        self.password_input = ModernInput("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        login_layout.addWidget(self.email_input)
        login_layout.addWidget(self.password_input)
        
        self.login_btn = ModernButton("Sign In", "primary")
        login_layout.addWidget(self.login_btn)
        
        email_layout.addWidget(login_group)
        
        # Registration form
        register_group = QWidget()
        register_layout = QVBoxLayout(register_group)
        
        register_title = QLabel("Create Account")
        register_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        register_title.setStyleSheet("color: #2d3748; margin-bottom: 8px;")
        register_layout.addWidget(register_title)
        
        self.reg_name_input = ModernInput("Full name")
        self.reg_email_input = ModernInput("Email address")
        self.reg_password_input = ModernInput("Password")
        self.reg_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        register_layout.addWidget(self.reg_name_input)
        register_layout.addWidget(self.reg_email_input)
        register_layout.addWidget(self.reg_password_input)
        
        self.register_btn = ModernButton("Create Account", "primary")
        register_layout.addWidget(self.register_btn)
        
        email_layout.addWidget(register_group)
        
        # Add tabs
        self.tab_widget.addTab(oauth_tab, "Quick Sign In")
        self.tab_widget.addTab(email_tab, "Email")
        
        content_layout.addWidget(self.tab_widget)
        main_layout.addWidget(content_card)
        
        # Status and progress
        status_card = ModernCard()
        status_layout = QVBoxLayout(status_card)
        
        self.status_label = QLabel("Initializing...")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setStyleSheet("color: #4a5568;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: rgba(200, 200, 200, 0.3);
                height: 8px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 4px;
            }
        """)
        status_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(status_card)
        
        # Privacy notice
        privacy_layout = QHBoxLayout()
        privacy_label = QLabel("🔒 <a href='#privacy' style='color: #667eea; text-decoration: none;'>Privacy & Data Protection</a>")
        privacy_label.setFont(QFont("Segoe UI", 9))
        privacy_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        privacy_label.linkActivated.connect(self.show_privacy_dialog)
        privacy_layout.addWidget(privacy_label)
        main_layout.addLayout(privacy_layout)
        
        self.setLayout(main_layout)
    
    def show_privacy_dialog(self):
        """Show GDPR privacy dialog"""
        dialog = GDPRDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.status_label.setText("Privacy preferences saved")
        else:
            self.status_label.setText("Privacy acceptance required for usage")
    
    def setup_ui(self):
        """Legacy method for compatibility - calls modern UI"""
        self.setup_modern_ui()
    
    def create_email_tab(self):
        """Create email authentication tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Login/Register toggle
        self.login_mode = True
        self.toggle_btn = QPushButton("Switch to Register")
        self.toggle_btn.clicked.connect(self.toggle_auth_mode)
        layout.addWidget(self.toggle_btn)
        
        # Form fields
        layout.addWidget(QLabel("Email:"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        layout.addWidget(self.email_input)
        
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter your password")
        layout.addWidget(self.password_input)
        
        # Name field (for registration)
        self.name_label = QLabel("Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your full name")
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)
        
        # Initially hide name field (login mode)
        self.name_label.hide()
        self.name_input.hide()
        
        # Submit button
        self.email_submit_btn = QPushButton("Sign In")
        self.email_submit_btn.clicked.connect(self.handle_email_auth)
        layout.addWidget(self.email_submit_btn)
        
        # Enable Enter key
        self.email_input.returnPressed.connect(self.handle_email_auth)
        self.password_input.returnPressed.connect(self.handle_email_auth)
        self.name_input.returnPressed.connect(self.handle_email_auth)
        
        widget.setLayout(layout)
        return widget
    
    def create_oauth_tab(self):
        """Create OAuth authentication tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Sign in with your Google account"))
        
        # OAuth button
        self.oauth_btn = QPushButton("Sign in with Google")
        self.oauth_btn.clicked.connect(self.handle_oauth_auth)
        self.oauth_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3367d6;
            }
        """)
        layout.addWidget(self.oauth_btn)
        
        # Info text
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(100)
        info_text.setText(
            "Google OAuth provides secure authentication without storing passwords. "
            "Your wellness data is kept private and only used for monitoring your well-being."
        )
        layout.addWidget(info_text)
        
        widget.setLayout(layout)
        return widget
    
    def setup_connections(self):
        """Setup signal connections for modern UI"""
        # Google OAuth button
        self.google_btn.clicked.connect(self.handle_oauth_auth)
        
        # Email login button
        self.login_btn.clicked.connect(self.handle_email_login)
        
        # Registration button
        self.register_btn.clicked.connect(self.handle_email_register)
        
        # Enter key shortcuts
        self.email_input.returnPressed.connect(self.handle_email_login)
        self.password_input.returnPressed.connect(self.handle_email_login)
        self.reg_email_input.returnPressed.connect(self.handle_email_register)
        self.reg_password_input.returnPressed.connect(self.handle_email_register)
    
    def handle_email_login(self):
        """Handle email login"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Error", "Please enter both email and password")
            return
        
        self.start_auth_process("email_login", email=email, password=password)
    
    def handle_email_register(self):
        """Handle email registration"""
        name = self.reg_name_input.text().strip()
        email = self.reg_email_input.text().strip()
        password = self.reg_password_input.text()
        
        if not name or not email or not password:
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return
        
        if len(password) < 8:
            QMessageBox.warning(self, "Error", "Password must be at least 8 characters")
            return
        
        self.start_auth_process("email_register", email=email, password=password, name=name)
    
    def handle_oauth_auth(self):
        """Handle OAuth authentication"""
        self.start_auth_process("oauth")
    
    def start_auth_process(self, auth_type, **kwargs):
        """Start authentication process with modern UI feedback"""
        # Disable all inputs
        self.google_btn.setEnabled(False)
        self.login_btn.setEnabled(False)
        self.register_btn.setEnabled(False)
        
        for input_field in [self.email_input, self.password_input, 
                           self.reg_name_input, self.reg_email_input, self.reg_password_input]:
            input_field.setEnabled(False)
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        if auth_type == "oauth":
            self.status_label.setText("🚀 Connecting with Google...")
        elif auth_type == "email_login":
            self.status_label.setText("🔐 Signing in...")
        elif auth_type == "email_register":
            self.status_label.setText("📝 Creating account...")
        
        # Start worker
        self.auth_worker = AuthWorker(auth_type, **kwargs)
        self.auth_worker.email_success.connect(self.on_auth_success)
        self.auth_worker.oauth_success.connect(self.on_auth_success)
        self.auth_worker.email_error.connect(self.on_auth_error)
        self.auth_worker.oauth_error.connect(self.on_auth_error)
        self.auth_worker.start()
    
    def reset_ui_state(self):
        """Reset UI to interactive state"""
        # Re-enable all inputs
        self.google_btn.setEnabled(True)
        self.login_btn.setEnabled(True)
        self.register_btn.setEnabled(True)
        
        for input_field in [self.email_input, self.password_input, 
                           self.reg_name_input, self.reg_email_input, self.reg_password_input]:
            input_field.setEnabled(True)
        
        # Hide progress
        self.progress_bar.setVisible(False)
    
    def try_auto_login(self):
        """Try to automatically login with stored credentials"""
        self.status_label.setText("🔍 Checking stored credentials...")
        self.progress_bar.setVisible(True)
        
        self.auth_worker = AuthWorker("auto_login")
        self.auth_worker.email_success.connect(self.on_auth_success)
        self.auth_worker.oauth_success.connect(self.on_auth_success)
        self.auth_worker.email_error.connect(self.on_auto_login_failed)
        
        # Set a timeout for auto-login
        QTimer.singleShot(5000, self.on_auto_login_timeout)
        self.auth_worker.start()
    
    def on_auto_login_failed(self, error_msg):
        """Handle failed auto-login"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("Please sign in")
        logger.debug(f"Auto-login failed: {error_msg}")
    
    def on_auto_login_timeout(self):
        """Handle auto-login timeout"""
        if self.auth_worker and self.auth_worker.isRunning():
            self.auth_worker.terminate()
        self.on_auto_login_failed("Auto-login timed out")
    
    def on_auth_success(self, user):
        """Handle successful authentication"""
        if user is None:
            self.on_auth_error("Authentication returned no user data")
            return
            
        self.user = user
        user_name = getattr(user, 'name', getattr(user, 'email', 'User'))
        self.status_label.setText(f"✅ Welcome, {user_name}!")
        self.progress_bar.setVisible(False)
        
        # Close dialog after a short delay
        QTimer.singleShot(1500, self.accept)
    
    def on_auth_error(self, error_msg):
        """Handle authentication error"""
        self.reset_ui_state()
        self.status_label.setText(f"❌ {error_msg}")
        
        # Show error message
        QMessageBox.warning(self, "Authentication Error", error_msg)
        self.status_label.setText("Please sign in")
        logger.info(f"Auto-login failed: {error_msg}")
    
    def on_auto_login_timeout(self):
        """Handle auto-login timeout"""
        if self.auth_worker and self.auth_worker.isRunning():
            self.auth_worker.terminate()
            self.progress_bar.hide()
            self.status_label.setText("Please sign in")
            logger.info("Auto-login timed out")
    
    def get_authenticated_user(self):
        """Get the authenticated user"""
        return self.user
