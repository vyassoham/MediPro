import os
import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from ocr_processor import OCRProcessor

def test_clean_extracted_text():
    """Verify that raw OCR text is cleaned up properly."""
    processor = OCRProcessor()
    
    # Test cleaning extra whitespaces and special characters
    raw_text = "  Paracetamol !!! 500mg \n \t  Tablet.   "
    cleaned = processor._clean_extracted_text(raw_text)
    assert cleaned == "Paracetamol 500mg Tablet."
    
    # Test cleaning of OCR artifacts (single character words, except digits)
    raw_artifact_text = "Paracetamol x 500mg y 1 tablet"
    cleaned_artifact = processor._clean_extracted_text(raw_artifact_text)
    assert cleaned_artifact == "Paracetamol 500mg 1 tablet"  # x and y filtered out, 1 remains

def test_calculate_medicine_confidence():
    """Verify confidence score calculations based on context and names."""
    processor = OCRProcessor()
    
    dosage_patterns = [r'\d+\s*mg\b', r'\d+\s*tablet']
    
    # Test common medicine with dosage nearby
    text = "Patient should take Paracetamol 500mg immediately"
    confidence = processor._calculate_medicine_confidence("Paracetamol", text, dosage_patterns)
    assert confidence > 0.8  # common name + dosage context bonus
    
    # Test uncommon word without dosage nearby
    text2 = "There is a warning about Lisinopril usage here"
    confidence2 = processor._calculate_medicine_confidence("Lisinopril", text2, dosage_patterns)
    assert 0.4 < confidence2 < 0.7  # basic match confidence without dosage boost
    
    # Test common medicine without dosage context
    text3 = "Avoid taking paracetamol with alcohol"
    confidence3 = processor._calculate_medicine_confidence("paracetamol", text3, dosage_patterns)
    assert confidence3 > 0.7  # common name bonus still boosts it


def test_identify_medicine_name():
    """Verify medicine name identification from text."""
    processor = OCRProcessor()
    
    text = "Rx: Metformin 500mg tablet twice daily. Also Ibuprofen 400mg."
    candidates = processor.identify_medicine_name(text)
    
    assert len(candidates) >= 2
    names = [c['name'].lower() for c in candidates]
    assert "metformin" in names
    assert "ibuprofen" in names

@patch('os.path.exists')
@patch('os.path.getsize')
def test_validate_image_file_invalid_paths(mock_getsize, mock_exists):
    """Verify image validation handles missing files and oversized images."""
    processor = OCRProcessor()
    
    # Case 1: File doesn't exist
    mock_exists.return_value = False
    is_valid, err = processor.validate_image_file("nonexistent.png")
    assert not is_valid
    assert "does not exist" in err
    
    # Case 2: File exists but too large
    mock_exists.return_value = True
    mock_getsize.return_value = 15 * 1024 * 1024  # 15MB
    is_valid, err = processor.validate_image_file("huge.png")
    assert not is_valid
    assert "too large" in err

@patch('os.path.exists')
@patch('os.path.getsize')
@patch('PIL.Image.open')
def test_validate_image_file_dimensions(mock_image_open, mock_getsize, mock_exists):
    """Verify image validation handles image dimensions and formats."""
    processor = OCRProcessor()
    mock_exists.return_value = True
    mock_getsize.return_value = 100 * 1024  # 100KB
    
    # Case 1: Image too small
    mock_img = MagicMock()
    mock_img.size = (40, 40)
    mock_image_open.return_value.__enter__.return_value = mock_img
    is_valid, err = processor.validate_image_file("small.png")
    assert not is_valid
    assert "too small" in err
    
    # Case 2: Supported image
    mock_img.size = (800, 600)
    mock_img.mode = "RGB"
    is_valid, err = processor.validate_image_file("valid.png")
    assert is_valid
    assert err == ""

@patch('cv2.imread')
@patch('cv2.resize')
@patch('cv2.cvtColor')
@patch('cv2.GaussianBlur')
@patch('cv2.adaptiveThreshold')
@patch('cv2.getStructuringElement')
@patch('cv2.morphologyEx')
@patch('cv2.medianBlur')
def test_preprocess_image(mock_median, mock_morph, mock_struct, mock_thresh, mock_blur, mock_color, mock_resize, mock_imread):
    """Verify that image preprocessing calls OpenCV functions correctly."""
    processor = OCRProcessor()
    
    # Mock return values for cv2 operations
    dummy_img = np.zeros((1000, 1000, 3), dtype=np.uint8)
    mock_imread.return_value = dummy_img
    mock_resize.return_value = np.zeros((800, 600, 3), dtype=np.uint8)
    mock_color.return_value = np.zeros((800, 600), dtype=np.uint8)
    mock_blur.return_value = np.zeros((800, 600), dtype=np.uint8)
    mock_thresh.return_value = np.zeros((800, 600), dtype=np.uint8)
    mock_morph.return_value = np.zeros((800, 600), dtype=np.uint8)
    mock_median.return_value = np.zeros((800, 600), dtype=np.uint8)
    
    res = processor.preprocess_image("test_image.png")
    
    assert res is not None
    mock_imread.assert_called_with("test_image.png")
    mock_resize.assert_called()
    mock_color.assert_called()
    mock_blur.assert_called()
    mock_thresh.assert_called()

@patch('ocr_processor.OCRProcessor.preprocess_image')
def test_process_medicine_image_pipeline(mock_preprocess, db):
    """Verify complete OCR pipeline from image input to database log."""
    processor = OCRProcessor()
    
    # Mock preprocessing success
    mock_preprocess.return_value = np.zeros((100, 100), dtype=np.uint8)
    
    # Process
    res = processor.process_medicine_image("test_image.png", database=db)
    
    assert res['processing_successful']
    assert "Paracetamol" in res['extracted_text']
    assert len(res['potential_medicines']) > 0
    assert res['potential_medicines'][0]['name'] == "Paracetamol"
    
    # Check that database save was called
    # conftest mocks pytesseract.image_to_string which returns Paracetamol
    assert db.connect()
    cursor = db.connection.cursor()
    cursor.execute("SELECT * FROM ocr_history WHERE image_path = 'test_image.png'")
    row = cursor.fetchone()
    assert row is not None
    assert row['recognized_medicine'] == "Paracetamol"
    db.disconnect()
