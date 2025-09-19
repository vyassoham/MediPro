"""
Configuration settings for Smart Medicine Reminder & Tracker
"""

import os

# Application Information
APP_NAME = "Smart Medicine Reminder & Tracker"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Soham Vyas"

# Database Configuration
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "medicine_tracker.db")

# OCR Configuration
TESSERACT_CONFIG = "--oem 3 --psm 6"  # OCR Engine Mode 3, Page Segmentation Mode 6
OCR_LANGUAGES = "eng"  # English language for OCR

# Image Processing Configuration
IMAGE_MAX_WIDTH = 800
IMAGE_MAX_HEIGHT = 600
PREPROCESSING_GAUSSIAN_BLUR = (5, 5)
PREPROCESSING_THRESHOLD = 127
PREPROCESSING_MAX_VALUE = 255

# GUI Configuration
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 600

# Reminder Configuration
REMINDER_SOUND_ENABLED = True
REMINDER_POPUP_DURATION = 30  # seconds
REMINDER_SNOOZE_DURATION = 10  # minutes

# Medicine Database API Configuration (for future API integration)
API_TIMEOUT = 30  # seconds
API_RETRY_ATTEMPTS = 3

# File Paths
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")
LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
EXPORTS_DIR = os.path.join(os.path.dirname(__file__), "exports")

# Create directories if they don't exist
for directory in [UPLOADS_DIR, LOGS_DIR, EXPORTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Supported image formats
SUPPORTED_IMAGE_FORMATS = [
    ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif"
]

# Medicine severity levels
MEDICINE_SEVERITY = {
    "mild": "Mild - Common OTC drug",
    "moderate": "Moderate - Prescription required", 
    "strong": "Strong - Requires medical supervision",
    "critical": "Critical - Hospital/specialist only"
}

# Age restrictions
AGE_RESTRICTIONS = {
    "all_ages": "Safe for all ages",
    "adults_only": "Adults only (18+)",
    "elderly_caution": "Use with caution in elderly",
    "children_only": "Children specific",
    "not_for_children": "Not suitable for children under 12"
}