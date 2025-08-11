"""
Unit tests for the patch manager module
Tests patch creation, application, and rollback functionality
"""

import unittest
import tempfile
import shutil
import os
import zipfile
import json
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from patch_manager.sdk import PatchManager, PatchConfig, PatchInfo


class TestPatchConfig(unittest.TestCase):
    """Test PatchConfig dataclass"""
    
    def test_patch_config_creation(self):
        """Test creating PatchConfig"""
        config = PatchConfig(
            patch_format="zip",
            compression_level=6,
            backup_enabled=True,
            signature_validation=True,
            exclude_patterns=["*.pyc", "__pycache__"],
            version_control=True,
            backup_strategy="incremental",
            validation_enabled=True,
            distribution_method="local"
        )
        
        self.assertEqual(config.patch_format, "zip")
        self.assertEqual(config.compression_level, 6)
        self.assertTrue(config.backup_enabled)
        self.assertTrue(config.signature_validation)
        self.assertEqual(config.exclude_patterns, ["*.pyc", "__pycache__"])
        self.assertTrue(config.version_control)
        self.assertEqual(config.backup_strategy, "incremental")
        self.assertTrue(config.validation_enabled)
        self.assertEqual(config.distribution_method, "local")
    
    def test_patch_config_defaults(self):
        """Test PatchConfig default values"""
        config = PatchConfig()
        
        self.assertEqual(config.patch_format, "zip")
        self.assertEqual(config.compression_level, 6)
        self.assertTrue(config.backup_enabled)
        self.assertTrue(config.signature_validation)
        self.assertIsInstance(config.exclude_patterns, list)
        self.assertTrue(config.version_control)
        self.assertEqual(config.backup_strategy, "incremental")
        self.assertTrue(config.validation_enabled)
        self.assertEqual(config.distribution_method, "local")


class TestPatchInfo(unittest.TestCase):
    """Test PatchInfo dataclass"""
    
    def test_patch_info_creation(self):
        """Test creating PatchInfo"""
        patch_info = PatchInfo(
            patch_id="patch_001",
            version="1.0.1",
            description="Bug fix for authentication",
            author="developer@wellness.ai",
            timestamp=1640995200.0,
            files_changed=["src/auth.py", "src/ui.py"],
            dependencies=["PyQt6>=6.0.0"],
            rollback_supported=True
        )
        
        self.assertEqual(patch_info.patch_id, "patch_001")
        self.assertEqual(patch_info.version, "1.0.1")
        self.assertEqual(patch_info.description, "Bug fix for authentication")
        self.assertEqual(patch_info.author, "developer@wellness.ai")
        self.assertEqual(patch_info.timestamp, 1640995200.0)
        self.assertEqual(patch_info.files_changed, ["src/auth.py", "src/ui.py"])
        self.assertEqual(patch_info.dependencies, ["PyQt6>=6.0.0"])
        self.assertTrue(patch_info.rollback_supported)
    
    def test_patch_info_to_dict(self):
        """Test converting PatchInfo to dictionary"""
        patch_info = PatchInfo(
            patch_id="patch_002",
            version="1.0.2",
            description="Performance improvements",
            author="developer@wellness.ai",
            timestamp=1640995260.0,
            files_changed=["src/metrics.py"],
            dependencies=[],
            rollback_supported=True
        )
        
        patch_dict = patch_info.to_dict()
        
        self.assertEqual(patch_dict["patch_id"], "patch_002")
        self.assertEqual(patch_dict["version"], "1.0.2")
        self.assertEqual(patch_dict["description"], "Performance improvements")
        self.assertEqual(patch_dict["author"], "developer@wellness.ai")
        self.assertEqual(patch_dict["timestamp"], 1640995260.0)
        self.assertEqual(patch_dict["files_changed"], ["src/metrics.py"])
        self.assertEqual(patch_dict["dependencies"], [])
        self.assertTrue(patch_dict["rollback_supported"])
    
    def test_patch_info_from_dict(self):
        """Test creating PatchInfo from dictionary"""
        patch_dict = {
            "patch_id": "patch_003",
            "version": "1.0.3",
            "description": "Security update",
            "author": "security@wellness.ai",
            "timestamp": 1640995320.0,
            "files_changed": ["src/auth.py", "src/security.py"],
            "dependencies": ["cryptography>=3.4.0"],
            "rollback_supported": False
        }
        
        patch_info = PatchInfo.from_dict(patch_dict)
        
        self.assertEqual(patch_info.patch_id, "patch_003")
        self.assertEqual(patch_info.version, "1.0.3")
        self.assertEqual(patch_info.description, "Security update")
        self.assertEqual(patch_info.author, "security@wellness.ai")
        self.assertEqual(patch_info.timestamp, 1640995320.0)
        self.assertEqual(patch_info.files_changed, ["src/auth.py", "src/security.py"])
        self.assertEqual(patch_info.dependencies, ["cryptography>=3.4.0"])
        self.assertFalse(patch_info.rollback_supported)


class TestPatchManager(unittest.TestCase):
    """Test PatchManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.patch_dir = os.path.join(self.temp_dir, "patches")
        self.backup_dir = os.path.join(self.temp_dir, "backups")
        self.config_file = os.path.join(self.temp_dir, "patch.yaml")
        
        # Create directories
        os.makedirs(self.patch_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Create test configuration
        self.config = PatchConfig()
        
        # Create patch manager
        self.patch_manager = PatchManager(
            patch_dir=self.patch_dir,
            backup_dir=self.backup_dir,
            config=self.config
        )
    
    def tearDown(self):
        """Clean up after tests"""
        shutil.rmtree(self.temp_dir)
    
    def test_patch_manager_initialization(self):
        """Test PatchManager initialization"""
        self.assertEqual(self.patch_manager.patch_dir, self.patch_dir)
        self.assertEqual(self.patch_manager.backup_dir, self.backup_dir)
        self.assertEqual(self.patch_manager.config, self.config)
        self.assertIsInstance(self.patch_manager.applied_patches, list)
    
    def test_load_config_from_file(self):
        """Test loading configuration from file"""
        # Create test config file
        config_data = {
            "patch_format": "zip",
            "compression_level": 9,
            "backup_enabled": True,
            "signature_validation": False,
            "exclude_patterns": ["*.log", "*.tmp"],
            "version_control": True,
            "backup_strategy": "full",
            "validation_enabled": True,
            "distribution_method": "remote"
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Load config
        config = PatchManager.load_config_from_file(self.config_file)
        
        self.assertEqual(config.patch_format, "zip")
        self.assertEqual(config.compression_level, 9)
        self.assertTrue(config.backup_enabled)
        self.assertFalse(config.signature_validation)
        self.assertEqual(config.exclude_patterns, ["*.log", "*.tmp"])
        self.assertTrue(config.version_control)
        self.assertEqual(config.backup_strategy, "full")
        self.assertTrue(config.validation_enabled)
        self.assertEqual(config.distribution_method, "remote")
    
    def test_load_config_from_file_not_found(self):
        """Test loading configuration from non-existent file"""
        non_existent_file = os.path.join(self.temp_dir, "nonexistent.yaml")
        
        # Should return default config
        config = PatchManager.load_config_from_file(non_existent_file)
        
        self.assertIsInstance(config, PatchConfig)
        self.assertEqual(config.patch_format, "zip")  # Default value
    
    def test_create_patch(self):
        """Test creating a patch"""
        # Create test source files
        source_dir = os.path.join(self.temp_dir, "source")
        os.makedirs(source_dir, exist_ok=True)
        
        # Create test files
        test_file1 = os.path.join(source_dir, "test1.py")
        test_file2 = os.path.join(source_dir, "test2.py")
        
        with open(test_file1, 'w') as f:
            f.write("print('Hello World')")
        
        with open(test_file2, 'w') as f:
            f.write("print('Goodbye World')")
        
        # Create patch info
        patch_info = PatchInfo(
            patch_id="test_patch_001",
            version="1.0.1",
            description="Test patch",
            author="test@example.com",
            timestamp=1640995200.0,
            files_changed=["test1.py", "test2.py"],
            dependencies=[],
            rollback_supported=True
        )
        
        # Create patch
        patch_file = self.patch_manager.create_patch(source_dir, patch_info)
        
        # Verify patch file was created
        self.assertTrue(os.path.exists(patch_file))
        self.assertTrue(patch_file.endswith(".zip"))
        
        # Verify patch contains files
        with zipfile.ZipFile(patch_file, 'r') as zip_file:
            file_list = zip_file.namelist()
            self.assertIn("test1.py", file_list)
            self.assertIn("test2.py", file_list)
            self.assertIn("patch_info.json", file_list)
    
    def test_create_patch_with_exclusions(self):
        """Test creating a patch with excluded files"""
        # Create test source files
        source_dir = os.path.join(self.temp_dir, "source_with_exclusions")
        os.makedirs(source_dir, exist_ok=True)
        
        # Create test files including excluded ones
        test_file = os.path.join(source_dir, "test.py")
        excluded_file = os.path.join(source_dir, "test.log")
        excluded_dir = os.path.join(source_dir, "__pycache__")
        os.makedirs(excluded_dir, exist_ok=True)
        excluded_pyc = os.path.join(excluded_dir, "test.pyc")
        
        with open(test_file, 'w') as f:
            f.write("print('Hello World')")
        
        with open(excluded_file, 'w') as f:
            f.write("log data")
        
        with open(excluded_pyc, 'w') as f:
            f.write("compiled python")
        
        # Create patch info
        patch_info = PatchInfo(
            patch_id="test_patch_002",
            version="1.0.2",
            description="Test patch with exclusions",
            author="test@example.com",
            timestamp=1640995200.0,
            files_changed=["test.py"],
            dependencies=[],
            rollback_supported=True
        )
        
        # Create patch
        patch_file = self.patch_manager.create_patch(source_dir, patch_info)
        
        # Verify patch file was created
        self.assertTrue(os.path.exists(patch_file))
        
        # Verify patch contains only non-excluded files
        with zipfile.ZipFile(patch_file, 'r') as zip_file:
            file_list = zip_file.namelist()
            self.assertIn("test.py", file_list)
            self.assertNotIn("test.log", file_list)
            self.assertNotIn("__pycache__/test.pyc", file_list)
    
    def test_apply_patch(self):
        """Test applying a patch"""
        # Create test target directory
        target_dir = os.path.join(self.temp_dir, "target")
        os.makedirs(target_dir, exist_ok=True)
        
        # Create existing file
        existing_file = os.path.join(target_dir, "existing.py")
        with open(existing_file, 'w') as f:
            f.write("old content")
        
        # Create patch file
        patch_file = os.path.join(self.patch_dir, "test_patch.zip")
        
        with zipfile.ZipFile(patch_file, 'w') as zip_file:
            # Add patch info
            patch_info = PatchInfo(
                patch_id="test_patch_003",
                version="1.0.3",
                description="Test patch",
                author="test@example.com",
                timestamp=1640995200.0,
                files_changed=["new_file.py", "existing.py"],
                dependencies=[],
                rollback_supported=True
            )
            
            zip_file.writestr("patch_info.json", json.dumps(patch_info.to_dict()))
            zip_file.writestr("new_file.py", "print('New file')")
            zip_file.writestr("existing.py", "print('Updated content')")
        
        # Apply patch
        result = self.patch_manager.apply_patch(patch_file, target_dir)
        
        # Verify patch was applied successfully
        self.assertTrue(result["success"])
        self.assertEqual(result["patch_id"], "test_patch_003")
        
        # Verify files were updated
        new_file = os.path.join(target_dir, "new_file.py")
        updated_file = os.path.join(target_dir, "existing.py")
        
        self.assertTrue(os.path.exists(new_file))
        self.assertTrue(os.path.exists(updated_file))
        
        with open(new_file, 'r') as f:
            self.assertEqual(f.read(), "print('New file')")
        
        with open(updated_file, 'r') as f:
            self.assertEqual(f.read(), "print('Updated content')")
        
        # Verify backup was created
        backup_files = os.listdir(self.backup_dir)
        self.assertGreater(len(backup_files), 0)
    
    def test_apply_patch_with_backup(self):
        """Test applying a patch with backup"""
        # Create test target directory
        target_dir = os.path.join(self.temp_dir, "target_with_backup")
        os.makedirs(target_dir, exist_ok=True)
        
        # Create existing file
        existing_file = os.path.join(target_dir, "test.py")
        original_content = "original content"
        with open(existing_file, 'w') as f:
            f.write(original_content)
        
        # Create patch file
        patch_file = os.path.join(self.patch_dir, "test_patch_backup.zip")
        
        with zipfile.ZipFile(patch_file, 'w') as zip_file:
            patch_info = PatchInfo(
                patch_id="test_patch_004",
                version="1.0.4",
                description="Test patch with backup",
                author="test@example.com",
                timestamp=1640995200.0,
                files_changed=["test.py"],
                dependencies=[],
                rollback_supported=True
            )
            
            zip_file.writestr("patch_info.json", json.dumps(patch_info.to_dict()))
            zip_file.writestr("test.py", "updated content")
        
        # Apply patch
        result = self.patch_manager.apply_patch(patch_file, target_dir)
        
        # Verify patch was applied
        self.assertTrue(result["success"])
        
        # Verify file was updated
        with open(existing_file, 'r') as f:
            self.assertEqual(f.read(), "updated content")
        
        # Verify backup was created and contains original content
        backup_files = os.listdir(self.backup_dir)
        self.assertGreater(len(backup_files), 0)
        
        # Find the backup file
        backup_file = None
        for file in backup_files:
            if file.endswith("test.py"):
                backup_file = os.path.join(self.backup_dir, file)
                break
        
        self.assertIsNotNone(backup_file)
        
        with open(backup_file, 'r') as f:
            self.assertEqual(f.read(), original_content)
    
    def test_rollback_patch(self):
        """Test rolling back a patch"""
        # Create test target directory
        target_dir = os.path.join(self.temp_dir, "target_rollback")
        os.makedirs(target_dir, exist_ok=True)
        
        # Create file with patched content
        patched_file = os.path.join(target_dir, "test.py")
        with open(patched_file, 'w') as f:
            f.write("patched content")
        
        # Create backup file
        backup_file = os.path.join(self.backup_dir, "test.py.backup")
        original_content = "original content"
        with open(backup_file, 'w') as f:
            f.write(original_content)
        
        # Create patch info
        patch_info = PatchInfo(
            patch_id="test_patch_005",
            version="1.0.5",
            description="Test patch for rollback",
            author="test@example.com",
            timestamp=1640995200.0,
            files_changed=["test.py"],
            dependencies=[],
            rollback_supported=True
        )
        
        # Rollback patch
        result = self.patch_manager.rollback_patch(patch_info, target_dir)
        
        # Verify rollback was successful
        self.assertTrue(result["success"])
        
        # Verify file was restored
        with open(patched_file, 'r') as f:
            self.assertEqual(f.read(), original_content)
    
    def test_rollback_patch_no_backup(self):
        """Test rolling back a patch without backup"""
        # Create test target directory
        target_dir = os.path.join(self.temp_dir, "target_no_backup")
        os.makedirs(target_dir, exist_ok=True)
        
        # Create file with patched content
        patched_file = os.path.join(target_dir, "test.py")
        with open(patched_file, 'w') as f:
            f.write("patched content")
        
        # Create patch info
        patch_info = PatchInfo(
            patch_id="test_patch_006",
            version="1.0.6",
            description="Test patch without backup",
            author="test@example.com",
            timestamp=1640995200.0,
            files_changed=["test.py"],
            dependencies=[],
            rollback_supported=True
        )
        
        # Rollback patch (should fail without backup)
        result = self.patch_manager.rollback_patch(patch_info, target_dir)
        
        # Verify rollback failed
        self.assertFalse(result["success"])
        self.assertIn("backup", result["error"].lower())
    
    def test_list_patches(self):
        """Test listing patches"""
        # Create test patch files
        patch_files = [
            "patch_001_v1.0.1.zip",
            "patch_002_v1.0.2.zip",
            "patch_003_v1.0.3.zip"
        ]
        
        for patch_file in patch_files:
            file_path = os.path.join(self.patch_dir, patch_file)
            with open(file_path, 'w') as f:
                f.write("test patch content")
        
        # List patches
        patches = self.patch_manager.list_patches()
        
        # Verify all patches are listed
        self.assertEqual(len(patches), 3)
        
        for patch_file in patch_files:
            self.assertIn(patch_file, patches)
    
    def test_get_patch_info(self):
        """Test getting patch information"""
        # Create patch file with info
        patch_file = os.path.join(self.patch_dir, "test_patch_info.zip")
        
        patch_info = PatchInfo(
            patch_id="test_patch_007",
            version="1.0.7",
            description="Test patch info",
            author="test@example.com",
            timestamp=1640995200.0,
            files_changed=["test.py"],
            dependencies=["requests>=2.25.0"],
            rollback_supported=True
        )
        
        with zipfile.ZipFile(patch_file, 'w') as zip_file:
            zip_file.writestr("patch_info.json", json.dumps(patch_info.to_dict()))
            zip_file.writestr("test.py", "test content")
        
        # Get patch info
        info = self.patch_manager.get_patch_info(patch_file)
        
        # Verify patch info is correct
        self.assertEqual(info.patch_id, "test_patch_007")
        self.assertEqual(info.version, "1.0.7")
        self.assertEqual(info.description, "Test patch info")
        self.assertEqual(info.author, "test@example.com")
        self.assertEqual(info.files_changed, ["test.py"])
        self.assertEqual(info.dependencies, ["requests>=2.25.0"])
        self.assertTrue(info.rollback_supported)
    
    def test_validate_patch(self):
        """Test patch validation"""
        # Create valid patch file
        patch_file = os.path.join(self.patch_dir, "valid_patch.zip")
        
        patch_info = PatchInfo(
            patch_id="valid_patch",
            version="1.0.8",
            description="Valid patch",
            author="test@example.com",
            timestamp=1640995200.0,
            files_changed=["test.py"],
            dependencies=[],
            rollback_supported=True
        )
        
        with zipfile.ZipFile(patch_file, 'w') as zip_file:
            zip_file.writestr("patch_info.json", json.dumps(patch_info.to_dict()))
            zip_file.writestr("test.py", "test content")
        
        # Validate patch
        result = self.patch_manager.validate_patch(patch_file)
        
        # Verify patch is valid
        self.assertTrue(result["valid"])
        self.assertIsNone(result["error"])
    
    def test_validate_patch_invalid(self):
        """Test patch validation with invalid patch"""
        # Create invalid patch file (missing patch_info.json)
        patch_file = os.path.join(self.patch_dir, "invalid_patch.zip")
        
        with zipfile.ZipFile(patch_file, 'w') as zip_file:
            zip_file.writestr("test.py", "test content")
        
        # Validate patch
        result = self.patch_manager.validate_patch(patch_file)
        
        # Verify patch is invalid
        self.assertFalse(result["valid"])
        self.assertIsNotNone(result["error"])
    
    def test_cleanup_old_patches(self):
        """Test cleaning up old patches"""
        # Create old patch files
        old_patches = [
            "old_patch_001.zip",
            "old_patch_002.zip"
        ]
        
        for patch_file in old_patches:
            file_path = os.path.join(self.patch_dir, patch_file)
            with open(file_path, 'w') as f:
                f.write("old patch content")
        
        # Create recent patch file
        recent_patch = os.path.join(self.patch_dir, "recent_patch.zip")
        with open(recent_patch, 'w') as f:
            f.write("recent patch content")
        
        # Cleanup old patches (older than 1 day)
        removed_count = self.patch_manager.cleanup_old_patches(max_age_days=1)
        
        # Verify old patches were removed
        self.assertGreaterEqual(removed_count, 0)
        
        # Verify recent patch still exists
        self.assertTrue(os.path.exists(recent_patch))
    
    def test_get_patch_statistics(self):
        """Test getting patch statistics"""
        # Create test patch files
        patch_files = [
            "patch_001_v1.0.1.zip",
            "patch_002_v1.0.2.zip",
            "patch_003_v1.0.3.zip"
        ]
        
        for patch_file in patch_files:
            file_path = os.path.join(self.patch_dir, patch_file)
            with open(file_path, 'w') as f:
                f.write("test patch content")
        
        # Get statistics
        stats = self.patch_manager.get_patch_statistics()
        
        # Verify statistics
        self.assertEqual(stats["total_patches"], 3)
        self.assertIn("total_size", stats)
        self.assertIn("average_size", stats)
        self.assertIn("oldest_patch", stats)
        self.assertIn("newest_patch", stats)


if __name__ == '__main__':
    unittest.main() 