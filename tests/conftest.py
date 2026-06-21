import os
import sys
import pytest
from unittest.mock import MagicMock

# Add repository root to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def temp_db_path(tmp_path):
    """Fixture to provide a temporary database path."""
    db_file = tmp_path / "test_medicine_tracker.db"
    return str(db_file)

@pytest.fixture
def db(temp_db_path):
    """Fixture to initialize a temporary test database."""
    from database import MedicineDatabase
    
    # Initialize database
    database = MedicineDatabase(db_path=temp_db_path)
    database.initialize_database()
    
    yield database
    
    # Ensure disconnected
    database.disconnect()
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except OSError:
            pass

@pytest.fixture(autouse=True)
def mock_notification(monkeypatch):
    """Fixture to mock desktop notifications globally for tests."""
    mock_notify = MagicMock()
    monkeypatch.setattr("plyer.notification.notify", mock_notify)
    return mock_notify

@pytest.fixture(autouse=True)
def mock_pytesseract(monkeypatch):
    """Fixture to mock pytesseract globally to avoid system tesseract dependency."""
    mock_img_to_str = MagicMock(return_value="Paracetamol 500mg Tablet\nTake 1 daily")
    mock_img_to_data = MagicMock(return_value={
        'level': [1], 'page_num': [1], 'block_num': [1], 'par_num': [1], 'line_num': [1],
        'word_num': [1], 'left': [10], 'top': [10], 'width': [100], 'height': [20],
        'conf': ['95'], 'text': ['Paracetamol']
    })
    
    monkeypatch.setattr("pytesseract.image_to_string", mock_img_to_str)
    monkeypatch.setattr("pytesseract.image_to_data", mock_img_to_data)
    
    return {
        'image_to_string': mock_img_to_str,
        'image_to_data': mock_img_to_data
    }
