import os
import config

def test_config_variables():
    """Verify essential config variables are defined and have expected formats."""
    assert config.APP_NAME == "Smart Medicine Reminder & Tracker"
    assert config.APP_VERSION == "1.0.0"
    assert config.IMAGE_MAX_WIDTH == 800
    assert config.IMAGE_MAX_HEIGHT == 600
    assert isinstance(config.SUPPORTED_IMAGE_FORMATS, list)
    assert ".png" in config.SUPPORTED_IMAGE_FORMATS
    assert ".jpg" in config.SUPPORTED_IMAGE_FORMATS

def test_directories_creation():
    """Verify config initializes application directories."""
    assert os.path.exists(config.UPLOADS_DIR)
    assert os.path.exists(config.LOGS_DIR)
    assert os.path.exists(config.EXPORTS_DIR)
    assert os.path.isdir(config.UPLOADS_DIR)
    assert os.path.isdir(config.LOGS_DIR)
    assert os.path.isdir(config.EXPORTS_DIR)
