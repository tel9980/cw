"""
Pytest configuration and shared fixtures.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from oxidation_workflow_v18.config import ConfigManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def test_config(temp_dir):
    """Create a test configuration manager with temporary paths."""
    config_path = temp_dir / "test_config.json"
    config = ConfigManager(str(config_path))
    
    # Set test paths
    config.config.storage.data_path = str(temp_dir / "data")
    config.config.storage.backup_path = str(temp_dir / "backups")
    config.config.storage.log_path = str(temp_dir / "logs")
    
    # Ensure directories exist
    config.config.storage.ensure_directories()
    
    return config


@pytest.fixture
def demo_mode_config(test_config):
    """Create a test configuration with demo mode enabled."""
    test_config.config.system.demo_mode = True
    return test_config
