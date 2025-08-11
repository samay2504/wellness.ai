"""
Test suite for authentication module
Tests Google OAuth2, user management, and secure token storage
"""

import unittest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import keyring
from google.oauth2.credentials import Credentials

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from desktop_app.auth import AuthManager, User, OAuthClient


class TestUser(unittest.TestCase):
    """Test User data model"""

    def test_user_creation(self):
        """Test creating a user with all fields"""
        user = User(
            id="test123",
            name="Test User",
            email="test@example.com",
            consent=True
        )
        
        self.assertEqual(user.id, "test123")
        self.assertEqual(user.name, "Test User")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.consent)

    def test_user_default_consent(self):
        """Test user creation with default consent value"""
        user = User(
            id="test123",
            name="Test User",
            email="test@example.com"
        )
        
        self.assertFalse(user.consent)


class TestOAuthClient(unittest.TestCase):
    """Test OAuth client functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.credentials_path = os.path.join(self.temp_dir, "credentials.json")
        
        # Create sample credentials file
        credentials_data = {
            "installed": {
                "client_id": "test-client-id.apps.googleusercontent.com",
                "project_id": "test-project",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": "test-secret",
                "redirect_uris": ["http://localhost"]
            }
        }
        
        with open(self.credentials_path, 'w') as f:
            json.dump(credentials_data, f)
        
        self.oauth_client = OAuthClient(self.credentials_path)

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('keyring.get_password')
    def test_load_credentials_success(self, mock_get_password):
        """Test successful credential loading"""
        # Mock stored token data
        token_data = {
            "token": "test-token",
            "refresh_token": "test-refresh-token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test-client-id.apps.googleusercontent.com",
            "client_secret": "test-secret",
            "scopes": ["https://www.googleapis.com/auth/userinfo.email"]
        }
        
        mock_get_password.return_value = json.dumps(token_data)
        
        credentials = self.oauth_client.load_credentials()
        
        self.assertIsNotNone(credentials)
        self.assertEqual(credentials.token, "test-token")
        mock_get_password.assert_called_once_with("wellness_ai", "oauth_token")

    @patch('keyring.get_password')
    def test_load_credentials_not_found(self, mock_get_password):
        """Test credential loading when no stored credentials exist"""
        mock_get_password.return_value = None
        
        credentials = self.oauth_client.load_credentials()
        
        self.assertIsNone(credentials)
        mock_get_password.assert_called_once_with("wellness_ai", "oauth_token")

    @patch('keyring.get_password')
    def test_load_credentials_invalid_json(self, mock_get_password):
        """Test credential loading with invalid JSON"""
        mock_get_password.return_value = "invalid-json"
        
        credentials = self.oauth_client.load_credentials()
        
        self.assertIsNone(credentials)

    @patch('google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file')
    @patch('webbrowser.open')
    def test_authenticate_new_user(self, mock_webbrowser, mock_flow):
        """Test authentication flow for new user"""
        # Mock flow
        mock_flow_instance = Mock()
        mock_flow_instance.run_local_server.return_value = Mock(
            token="new-token",
            refresh_token="new-refresh-token",
            token_uri="https://oauth2.googleapis.com/token",
            client_id="test-client-id.apps.googleusercontent.com",
            client_secret="test-secret",
            scopes=["https://www.googleapis.com/auth/userinfo.email"]
        )
        mock_flow.return_value = mock_flow_instance
        
        # Mock user info
        mock_user_info = {
            "id": "test123",
            "name": "Test User",
            "email": "test@example.com"
        }
        
        with patch.object(self.oauth_client, '_get_user_info', return_value=mock_user_info):
            user = self.oauth_client.authenticate()
        
        self.assertIsNotNone(user)
        self.assertEqual(user.id, "test123")
        self.assertEqual(user.name, "Test User")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.consent)

    @patch('keyring.set_password')
    def test_save_credentials(self, mock_set_password):
        """Test saving credentials to secure storage"""
        credentials = Mock(
            token="test-token",
            refresh_token="test-refresh-token",
            token_uri="https://oauth2.googleapis.com/token",
            client_id="test-client-id.apps.googleusercontent.com",
            client_secret="test-secret",
            scopes=["https://www.googleapis.com/auth/userinfo.email"]
        )
        
        self.oauth_client.save_credentials(credentials)
        
        # Verify keyring was called with correct parameters
        mock_set_password.assert_called_once()
        call_args = mock_set_password.call_args
        self.assertEqual(call_args[0][0], "wellness_ai")
        self.assertEqual(call_args[0][1], "oauth_token")
        
        # Verify stored data contains expected fields
        stored_data = json.loads(call_args[0][2])
        self.assertEqual(stored_data["token"], "test-token")
        self.assertEqual(stored_data["refresh_token"], "test-refresh-token")


class TestAuthManager(unittest.TestCase):
    """Test authentication manager"""

    def setUp(self):
        """Set up test fixtures"""
        self.auth_manager = AuthManager()

    @patch('desktop_app.auth.OAuthClient')
    def test_init(self, mock_oauth_client):
        """Test AuthManager initialization"""
        auth_manager = AuthManager()
        
        self.assertIsNotNone(auth_manager)
        mock_oauth_client.assert_called_once()

    @patch.object(AuthManager, '_load_user_from_storage')
    def test_get_current_user_not_authenticated(self, mock_load_user):
        """Test getting current user when not authenticated"""
        mock_load_user.return_value = None
        
        user = self.auth_manager.get_current_user()
        
        self.assertIsNone(user)
        mock_load_user.assert_called_once()

    @patch.object(AuthManager, '_load_user_from_storage')
    def test_get_current_user_authenticated(self, mock_load_user):
        """Test getting current user when authenticated"""
        mock_user = User(
            id="test123",
            name="Test User",
            email="test@example.com",
            consent=True
        )
        mock_load_user.return_value = mock_user
        
        user = self.auth_manager.get_current_user()
        
        self.assertEqual(user, mock_user)
        mock_load_user.assert_called_once()

    @patch.object(AuthManager, '_save_user_to_storage')
    @patch.object(AuthManager, '_load_user_from_storage')
    def test_sign_in_success(self, mock_load_user, mock_save_user):
        """Test successful sign in"""
        mock_load_user.return_value = None  # No existing user
        
        mock_user = User(
            id="test123",
            name="Test User",
            email="test@example.com",
            consent=True
        )
        
        with patch.object(self.auth_manager.oauth_client, 'authenticate', return_value=mock_user):
            result = self.auth_manager.sign_in()
        
        self.assertTrue(result)
        mock_save_user.assert_called_once_with(mock_user)

    @patch.object(AuthManager, '_load_user_from_storage')
    def test_sign_in_already_authenticated(self, mock_load_user):
        """Test sign in when already authenticated"""
        mock_user = User(
            id="test123",
            name="Test User",
            email="test@example.com",
            consent=True
        )
        mock_load_user.return_value = mock_user
        
        result = self.auth_manager.sign_in()
        
        self.assertTrue(result)

    @patch.object(AuthManager, '_save_user_to_storage')
    @patch.object(AuthManager, '_load_user_from_storage')
    def test_sign_in_authentication_failed(self, mock_load_user, mock_save_user):
        """Test sign in when authentication fails"""
        mock_load_user.return_value = None
        
        with patch.object(self.auth_manager.oauth_client, 'authenticate', return_value=None):
            result = self.auth_manager.sign_in()
        
        self.assertFalse(result)
        mock_save_user.assert_not_called()

    @patch('keyring.delete_password')
    @patch.object(AuthManager, '_save_user_to_storage')
    def test_sign_out(self, mock_save_user, mock_delete_password):
        """Test sign out functionality"""
        # Set up a current user
        mock_user = User(
            id="test123",
            name="Test User",
            email="test@example.com",
            consent=True
        )
        self.auth_manager._current_user = mock_user
        
        self.auth_manager.sign_out()
        
        # Verify user is cleared
        self.assertIsNone(self.auth_manager._current_user)
        
        # Verify credentials are deleted
        mock_delete_password.assert_called_once_with("wellness_ai", "oauth_token")
        
        # Verify user storage is cleared
        mock_save_user.assert_called_once_with(None)

    @patch('keyring.get_password')
    def test_load_user_from_storage_success(self, mock_get_password):
        """Test loading user from storage successfully"""
        user_data = {
            "id": "test123",
            "name": "Test User",
            "email": "test@example.com",
            "consent": True
        }
        mock_get_password.return_value = json.dumps(user_data)
        
        user = self.auth_manager._load_user_from_storage()
        
        self.assertIsNotNone(user)
        self.assertEqual(user.id, "test123")
        self.assertEqual(user.name, "Test User")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.consent)

    @patch('keyring.get_password')
    def test_load_user_from_storage_not_found(self, mock_get_password):
        """Test loading user when not found in storage"""
        mock_get_password.return_value = None
        
        user = self.auth_manager._load_user_from_storage()
        
        self.assertIsNone(user)

    @patch('keyring.set_password')
    def test_save_user_to_storage(self, mock_set_password):
        """Test saving user to storage"""
        user = User(
            id="test123",
            name="Test User",
            email="test@example.com",
            consent=True
        )
        
        self.auth_manager._save_user_to_storage(user)
        
        mock_set_password.assert_called_once_with("wellness_ai", "user_data", json.dumps({
            "id": "test123",
            "name": "Test User",
            "email": "test@example.com",
            "consent": True
        }))

    @patch('keyring.set_password')
    def test_save_user_to_storage_none(self, mock_set_password):
        """Test saving None user to storage (clearing)"""
        self.auth_manager._save_user_to_storage(None)
        
        mock_set_password.assert_called_once_with("wellness_ai", "user_data", "")


if __name__ == '__main__':
    unittest.main() 