#!/usr/bin/env python3
"""
Email Authentication Dialog for Wellness at Work Desktop Application
"""

import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QFormLayout, QMessageBox)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class EmailAuthDialog(QDialog):
    """Dialog for email/password authentication"""
    
    # Signals
    login_success = pyqtSignal(dict)  # User data
    
    def __init__(self, parent=None, mode='login'):
        super().__init__(parent)
        self.mode = mode
        self.setWindowTitle("Email Login" if mode == 'login' else "Email Signup")
        self.setModal(True)
        self.setFixedSize(400, 300)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout()
        
        # Title
        title_text = "Sign In with Email" if self.mode == 'login' else "Sign Up with Email"
        title = QLabel(title_text)
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin: 20px 0;")
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email address")
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        form_layout.addRow("Email:", self.email_input)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        form_layout.addRow("Password:", self.password_input)
        
        layout.addLayout(form_layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #e74c3c; margin: 10px 0;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.login_button = QPushButton("Sign In")
        self.login_button.clicked.connect(self._handle_login)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        button_layout.addWidget(self.login_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect Enter key to login
        self.password_input.returnPressed.connect(self._handle_login)
        self.email_input.returnPressed.connect(self._handle_login)
    
    def _handle_login(self):
        """Handle login button click"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        # Basic validation
        if not email:
            self._show_error("Please enter your email address")
            return
        
        if not password:
            self._show_error("Please enter your password")
            return
        
        if "@" not in email:
            self._show_error("Please enter a valid email address")
            return
        
        # Disable button during login
        self.login_button.setEnabled(False)
        self.login_button.setText("Signing in...")
        self.status_label.setText("Authenticating...")
        
        try:
            # For demo purposes, create a mock user
            # In production, this would authenticate with a backend service
            user_data = {
                "id": f"user_{hash(email) % 1000000}",
                "name": email.split("@")[0].title(),
                "email": email,
                "consent": True,
                "auth_method": "email"
            }
            
            # Simulate authentication delay
            import time
            time.sleep(0.5)
            
            # Emit success signal
            self.login_success.emit(user_data)
            self.accept()
            
        except Exception as e:
            logger.error(f"Email authentication error: {e}")
            self._show_error("Authentication failed. Please try again.")
        finally:
            self.login_button.setEnabled(True)
            self.login_button.setText("Sign In")
    
    def _show_error(self, message):
        """Show error message"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #e74c3c; margin: 10px 0;")
    
    def clear_form(self):
        """Clear the form inputs"""
        self.email_input.clear()
        self.password_input.clear()
        self.status_label.clear()
    
    def get_credentials(self):
        """Get the entered credentials"""
        return self.email_input.text(), self.password_input.text(), True
