"""
OCR Processing module for Smart Medicine Reminder & Tracker
Handles image preprocessing and text extraction from medicine strips and prescriptions
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance
import re
import os
import shutil
from config import (
    TESSERACT_CONFIG, OCR_LANGUAGES, IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT,
    PREPROCESSING_GAUSSIAN_BLUR, PREPROCESSING_THRESHOLD, PREPROCESSING_MAX_VALUE
)


class OCRProcessor:
    """Handles OCR processing for medicine recognition from images."""
    
    def __init__(self):
        """Initialize OCR processor with configuration and binary discovery."""
        self.tesseract_config = TESSERACT_CONFIG
        self.languages = OCR_LANGUAGES
        self._configure_tesseract_path()
        
    def _configure_tesseract_path(self):
        """Auto-detect and configure Tesseract executable across platforms."""
        current_cmd = getattr(pytesseract.pytesseract, "tesseract_cmd", "tesseract")
        if shutil.which(current_cmd) or os.path.isfile(current_cmd):
            return

        # Check standard Windows paths
        standard_windows_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\Tesseract-OCR\tesseract.exe"),
        ]
        for p in standard_windows_paths:
            if os.path.isfile(p):
                pytesseract.pytesseract.tesseract_cmd = p
                return

    @staticmethod
    def is_tesseract_available() -> bool:
        """Check if Tesseract OCR binary is installed and executable."""
        cmd = getattr(pytesseract.pytesseract, "tesseract_cmd", "tesseract")
        return bool(shutil.which(cmd) or os.path.isfile(cmd))
        
    def preprocess_image(self, image_path):
        """
        Preprocess image for better OCR accuracy.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            numpy.ndarray: Preprocessed image
        """
        try:
            # Read image using OpenCV
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            # Resize image if too large
            height, width = image.shape[:2]
            if width > IMAGE_MAX_WIDTH or height > IMAGE_MAX_HEIGHT:
                scale = min(IMAGE_MAX_WIDTH / width, IMAGE_MAX_HEIGHT / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, PREPROCESSING_GAUSSIAN_BLUR, 0)
            
            # Apply adaptive threshold for better text contrast
            thresh = cv2.adaptiveThreshold(
                blurred, PREPROCESSING_MAX_VALUE, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Apply morphological operations to clean up the image
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Denoise
            denoised = cv2.medianBlur(cleaned, 3)
            
            return denoised
            
        except Exception as e:
            print(f"Image preprocessing error: {e}")
            return None
    
    def extract_text(self, image_path):
        """
        Extract text from medicine image using OCR.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            tuple: (extracted_text, confidence_score)
        """
        try:
            # Preprocess the image
            processed_image = self.preprocess_image(image_path)
            if processed_image is None:
                return "", 0.0
            
            # Convert to PIL Image for pytesseract
            pil_image = Image.fromarray(processed_image)
            
            # Enhance image contrast
            enhancer = ImageEnhance.Contrast(pil_image)
            enhanced_image = enhancer.enhance(2.0)
            
            # Extract text using pytesseract
            extracted_text = pytesseract.image_to_string(
                enhanced_image, 
                lang=self.languages, 
                config=self.tesseract_config
            )
            
            # Get confidence scores
            try:
                data = pytesseract.image_to_data(
                    enhanced_image, 
                    lang=self.languages, 
                    config=self.tesseract_config,
                    output_type=pytesseract.Output.DICT
                )
                
                # Calculate average confidence for detected text
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                
            except Exception:
                avg_confidence = 0.0
            
            # Clean up extracted text
            cleaned_text = self._clean_extracted_text(extracted_text)
            
            return cleaned_text, avg_confidence
            
        except Exception as e:
            print(f"Text extraction error: {e}")
            if "tesseract is not installed" in str(e).lower() or not self.is_tesseract_available():
                print("Tesseract OCR engine is not installed or not in system PATH.")
            return "", 0.0
    
    def _clean_extracted_text(self, text):
        """
        Clean and normalize extracted text.
        
        Args:
            text (str): Raw extracted text
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters but keep alphanumeric, spaces, and common punctuation
        cleaned = re.sub(r'[^\w\s\-\.\(\)\/]', '', cleaned)
        
        # Remove single characters that are likely OCR artifacts
        words = cleaned.split()
        filtered_words = [word for word in words if len(word) > 1 or word.isdigit()]
        
        return ' '.join(filtered_words)
    
    def identify_medicine_name(self, extracted_text):
        """
        Identify potential medicine names from extracted text.
        
        Args:
            extracted_text (str): Text extracted from image
            
        Returns:
            list: List of potential medicine names with confidence scores
        """
        if not extracted_text:
            return []
        
        potential_medicines = []
        words = extracted_text.split()
        
        # Common medicine name patterns
        medicine_patterns = [
            r'\b[A-Z][a-z]+(?:cillin|mycin|prazole|dipine|sartan|olol|pril|ide)\b',  # Common suffixes
            r'\b(?:Paracetamol|Ibuprofen|Aspirin|Amoxicillin|Metformin|Atorvastatin)\b',  # Common names
            r'\b[A-Z][a-z]{3,}(?:\s+[A-Z][a-z]+)?\b',  # Capitalized words (potential brand names)
        ]
        
        # Look for dosage information to help identify medicine context
        dosage_patterns = [
            r'\d+\s*mg\b',
            r'\d+\s*mcg\b',
            r'\d+\s*g\b',
            r'\d+\s*ml\b',
            r'\d+\s*tablet',
            r'\d+\s*capsule'
        ]
        
        # Find medicines using patterns
        for pattern in medicine_patterns:
            matches = re.finditer(pattern, extracted_text, re.IGNORECASE)
            for match in matches:
                medicine_name = match.group().strip()
                
                # Calculate confidence based on context
                confidence = self._calculate_medicine_confidence(medicine_name, extracted_text, dosage_patterns)
                
                if confidence > 0.3:  # Minimum confidence threshold
                    potential_medicines.append({
                        'name': medicine_name,
                        'confidence': confidence,
                        'context': extracted_text
                    })
        
        # Sort by confidence and remove duplicates
        unique_medicines = {}
        for med in potential_medicines:
            name_lower = med['name'].lower()
            if name_lower not in unique_medicines or med['confidence'] > unique_medicines[name_lower]['confidence']:
                unique_medicines[name_lower] = med
        
        # Sort by confidence descending
        sorted_medicines = sorted(unique_medicines.values(), key=lambda x: x['confidence'], reverse=True)
        
        return sorted_medicines[:5]  # Return top 5 candidates
    
    def _calculate_medicine_confidence(self, medicine_name, full_text, dosage_patterns):
        """
        Calculate confidence score for a potential medicine name.
        
        Args:
            medicine_name (str): Potential medicine name
            full_text (str): Full extracted text
            dosage_patterns (list): List of dosage regex patterns
            
        Returns:
            float: Confidence score between 0 and 1
        """
        confidence = 0.5  # Base confidence
        
        # Boost confidence if dosage information is found nearby
        words = full_text.split()
        try:
            med_index = words.index(medicine_name)
            
            # Check words around the medicine name for dosage info
            context_window = 3
            start_idx = max(0, med_index - context_window)
            end_idx = min(len(words), med_index + context_window + 1)
            context = ' '.join(words[start_idx:end_idx])
            
            for pattern in dosage_patterns:
                if re.search(pattern, context, re.IGNORECASE):
                    confidence += 0.2
                    break
                    
        except ValueError:
            pass
        
        # Boost confidence for known medicine name patterns
        if len(medicine_name) >= 5:
            confidence += 0.1
            
        # Check if it's a common medicine name
        common_medicines = [
            'paracetamol', 'ibuprofen', 'aspirin', 'amoxicillin', 'metformin',
            'atorvastatin', 'omeprazole', 'amlodipine', 'losartan', 'simvastatin'
        ]
        
        if medicine_name.lower() in common_medicines:
            confidence += 0.3
        
        return min(confidence, 1.0)
    
    def process_medicine_image(self, image_path, database=None):
        """
        Complete processing pipeline for medicine image.
        
        Args:
            image_path (str): Path to the medicine image
            database: Database instance for saving results
            
        Returns:
            dict: Processing results including extracted text and identified medicines
        """
        try:
            # Extract text from image
            extracted_text, confidence = self.extract_text(image_path)
            
            # Identify potential medicine names
            potential_medicines = self.identify_medicine_name(extracted_text)
            
            # Prepare results
            results = {
                'image_path': image_path,
                'extracted_text': extracted_text,
                'ocr_confidence': confidence,
                'potential_medicines': potential_medicines,
                'processing_successful': True
            }
            
            # Save to database if provided
            if database and potential_medicines:
                best_match = potential_medicines[0]['name']
                database.save_ocr_result(
                    image_path, extracted_text, best_match, confidence
                )
            
            return results
            
        except Exception as e:
            print(f"Medicine image processing error: {e}")
            return {
                'image_path': image_path,
                'extracted_text': "",
                'ocr_confidence': 0.0,
                'potential_medicines': [],
                'processing_successful': False,
                'error': str(e)
            }
    
    def validate_image_file(self, image_path):
        """
        Validate if the image file is suitable for OCR processing.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                return False, "Image file does not exist"
            
            # Check file size (max 10MB)
            file_size = os.path.getsize(image_path)
            if file_size > 10 * 1024 * 1024:
                return False, "Image file is too large (max 10MB)"
            
            # Try to open with PIL
            with Image.open(image_path) as img:
                # Check image dimensions
                width, height = img.size
                if width < 50 or height < 50:
                    return False, "Image is too small (minimum 50x50 pixels)"
                
                if width > 5000 or height > 5000:
                    return False, "Image is too large (maximum 5000x5000 pixels)"
                
                # Check if image has readable content
                if img.mode not in ['RGB', 'RGBA', 'L', 'P']:
                    return False, "Unsupported image format"
            
            return True, ""
            
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"