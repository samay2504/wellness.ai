"""
Patch Manager CLI for Wellness at Work
Command-line interface for creating and applying patches
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from .sdk import PatchManager

logger = logging.getLogger(__name__)


def create_patch(version: str, base_dir: Path) -> Path:
    """
    Compute diff from last tag
    Write delta package
    """
    try:
        pm = PatchManager()
        package_path = pm.create_patch(version, base_dir)
        logger.info(f"Patch created: {package_path}")
        return package_path
    except Exception as e:
        logger.error(f"Failed to create patch: {e}")
        raise


def apply_patch(package_path: Path) -> bool:
    """
    Unpack & apply changes
    """
    try:
        pm = PatchManager()
        success = pm.apply_patch(package_path)
        if success:
            logger.info(f"Patch applied successfully: {package_path}")
        else:
            logger.error(f"Failed to apply patch: {package_path}")
        return success
    except Exception as e:
        logger.error(f"Error applying patch: {e}")
        return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Wellness at Work Patch Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize patch repository")
    init_parser.add_argument("--config", type=str, default="configs/patch.yaml",
                           help="Configuration file path")
    
    # Create patch command
    create_parser = subparsers.add_parser("create-patch", help="Create new patch")
    create_parser.add_argument("--version", type=str, required=True,
                              help="Version number (e.g., v1.0.1)")
    create_parser.add_argument("--base-dir", type=str, default=".",
                              help="Base directory for patch creation")
    create_parser.add_argument("--output", type=str, help="Output path for patch")
    
    # Apply patch command
    apply_parser = subparsers.add_parser("apply-patch", help="Apply patch")
    apply_parser.add_argument("package_path", type=str, help="Path to patch package")
    apply_parser.add_argument("--backup", action="store_true", help="Create backup before applying")
    
    # Rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback to previous version")
    rollback_parser.add_argument("--to", type=str, required=True,
                                help="Version to rollback to")
    rollback_parser.add_argument("--force", action="store_true", help="Force rollback")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available patches")
    list_parser.add_argument("--installed", action="store_true", help="Show installed patches only")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        if args.command == "init":
            pm = PatchManager()
            pm.init_repository(args.config)
            print("Patch repository initialized successfully")
            
        elif args.command == "create-patch":
            base_dir = Path(args.base_dir)
            if not base_dir.exists():
                print(f"Error: Base directory does not exist: {base_dir}")
                return 1
            
            package_path = create_patch(args.version, base_dir)
            if args.output:
                import shutil
                shutil.move(str(package_path), args.output)
                package_path = Path(args.output)
            
            print(f"Patch created: {package_path}")
            
        elif args.command == "apply-patch":
            package_path = Path(args.package_path)
            if not package_path.exists():
                print(f"Error: Patch file does not exist: {package_path}")
                return 1
            
            success = apply_patch(package_path)
            return 0 if success else 1
            
        elif args.command == "rollback":
            pm = PatchManager()
            success = pm.rollback(args.to, force=args.force)
            if success:
                print(f"Successfully rolled back to version: {args.to}")
            else:
                print(f"Failed to rollback to version: {args.to}")
                return 1
                
        elif args.command == "list":
            pm = PatchManager()
            patches = pm.list_patches(installed_only=args.installed)
            if patches:
                print("Available patches:")
                for patch in patches:
                    print(f"  - {patch['version']} ({patch['date']})")
            else:
                print("No patches found")
        
        return 0
        
    except Exception as e:
        logger.error(f"Command failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 