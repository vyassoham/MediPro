"""
Database module for Smart Medicine Reminder & Tracker
Handles SQLite database operations for medicine information and user data
"""

import sqlite3
import datetime
import os
from config import DATABASE_PATH, MEDICINE_SEVERITY, AGE_RESTRICTIONS


class MedicineDatabase:
    """Handles all database operations for the medicine tracker application."""
    
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.connection = None
        
    def connect(self):
        """Establish database connection."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            return True
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def initialize_database(self):
        """Create database tables and populate with initial medicine data."""
        if not self.connect():
            raise Exception("Failed to connect to database")
        
        try:
            cursor = self.connection.cursor()
            
            # Create medicines table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS medicines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    generic_name TEXT,
                    dosage_form TEXT,
                    strength TEXT,
                    description TEXT,
                    usage_instructions TEXT,
                    dosage_adult TEXT,
                    dosage_children TEXT,
                    side_effects TEXT,
                    warnings TEXT,
                    contraindications TEXT,
                    age_restriction TEXT,
                    severity TEXT,
                    prescription_required BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create user_medicines table (for tracking user's current medicines)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_medicines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    medicine_id INTEGER,
                    user_dosage TEXT,
                    frequency TEXT,
                    start_date DATE,
                    end_date DATE,
                    notes TEXT,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (medicine_id) REFERENCES medicines (id)
                )
            ''')
            
            # Create reminders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_medicine_id INTEGER,
                    reminder_time TIME,
                    frequency TEXT,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_medicine_id) REFERENCES user_medicines (id)
                )
            ''')
            
            # Create medicine_logs table (for tracking when medicines were taken)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS medicine_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_medicine_id INTEGER,
                    taken_at TIMESTAMP,
                    scheduled_time TIMESTAMP,
                    status TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_medicine_id) REFERENCES user_medicines (id)
                )
            ''')
            
            # Create ocr_history table (for storing OCR processing history)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ocr_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT,
                    extracted_text TEXT,
                    recognized_medicine TEXT,
                    confidence_score REAL,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.connection.commit()
            
            # Populate with sample medicine data
            self._populate_sample_medicines()
            
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
            raise
        finally:
            self.disconnect()
    
    def _populate_sample_medicines(self):
        """Populate database with comprehensive medicine data."""
        sample_medicines = [
            {
                'name': 'Paracetamol',
                'generic_name': 'Acetaminophen',
                'dosage_form': 'Tablet',
                'strength': '500mg',
                'description': 'Pain reliever and fever reducer',
                'usage_instructions': 'Take with or without food. Do not exceed 4g per day.',
                'dosage_adult': '500-1000mg every 4-6 hours, maximum 4g/day',
                'dosage_children': '10-15mg/kg every 4-6 hours',
                'side_effects': 'Rare: nausea, skin rash. Overdose can cause liver damage.',
                'warnings': 'Do not exceed recommended dose. Avoid alcohol.',
                'contraindications': 'Severe liver disease',
                'age_restriction': 'all_ages',
                'severity': 'mild',
                'prescription_required': False
            },
            {
                'name': 'Acetaminophen',
                'generic_name': 'Acetaminophen',
                'dosage_form': 'Tablet',
                'strength': '325mg',
                'description': 'Pain reliever and fever reducer (generic paracetamol)',
                'usage_instructions': 'Take with or without food. Do not exceed 4g per day.',
                'dosage_adult': '325-650mg every 4-6 hours, maximum 4g/day',
                'dosage_children': '10-15mg/kg every 4-6 hours',
                'side_effects': 'Rare: nausea, skin rash. Overdose can cause liver damage.',
                'warnings': 'Do not exceed recommended dose. Avoid alcohol.',
                'contraindications': 'Severe liver disease',
                'age_restriction': 'all_ages',
                'severity': 'mild',
                'prescription_required': False
            },
            {
                'name': 'Tylenol',
                'generic_name': 'Acetaminophen',
                'dosage_form': 'Tablet',
                'strength': '500mg',
                'description': 'Brand name acetaminophen for pain and fever',
                'usage_instructions': 'Take with or without food. Do not exceed 4g per day.',
                'dosage_adult': '500-1000mg every 4-6 hours, maximum 4g/day',
                'dosage_children': '10-15mg/kg every 4-6 hours',
                'side_effects': 'Rare: nausea, skin rash. Overdose can cause liver damage.',
                'warnings': 'Do not exceed recommended dose. Avoid alcohol.',
                'contraindications': 'Severe liver disease',
                'age_restriction': 'all_ages',
                'severity': 'mild',
                'prescription_required': False
            },
            {
                'name': 'Ibuprofen',
                'generic_name': 'Ibuprofen',
                'dosage_form': 'Tablet',
                'strength': '400mg',
                'description': 'Anti-inflammatory pain reliever',
                'usage_instructions': 'Take with food to reduce stomach irritation.',
                'dosage_adult': '200-400mg every 4-6 hours, maximum 1.2g/day',
                'dosage_children': '5-10mg/kg every 6-8 hours',
                'side_effects': 'Stomach upset, heartburn, dizziness, headache',
                'warnings': 'May increase risk of heart attack or stroke. Avoid if pregnant.',
                'contraindications': 'Active peptic ulcer, severe heart failure',
                'age_restriction': 'not_for_children',
                'severity': 'moderate',
                'prescription_required': False
            },
            {
                'name': 'Amoxicillin',
                'generic_name': 'Amoxicillin',
                'dosage_form': 'Capsule',
                'strength': '250mg',
                'description': 'Antibiotic for bacterial infections',
                'usage_instructions': 'Complete full course even if feeling better.',
                'dosage_adult': '250-500mg every 8 hours',
                'dosage_children': '20-40mg/kg/day divided into 3 doses',
                'side_effects': 'Diarrhea, nausea, skin rash, allergic reactions',
                'warnings': 'Tell doctor about penicillin allergies',
                'contraindications': 'Penicillin allergy',
                'age_restriction': 'all_ages',
                'severity': 'moderate',
                'prescription_required': True
            },
            {
                'name': 'Aspirin',
                'generic_name': 'Acetylsalicylic Acid',
                'dosage_form': 'Tablet',
                'strength': '75mg',
                'description': 'Blood thinner and pain reliever',
                'usage_instructions': 'Take with food. Low dose for heart protection.',
                'dosage_adult': '75-100mg daily for cardiovascular protection',
                'dosage_children': 'Not recommended under 16 years',
                'side_effects': 'Stomach bleeding, bruising, ringing in ears',
                'warnings': 'Risk of bleeding. Avoid before surgery.',
                'contraindications': 'Active bleeding, severe liver disease',
                'age_restriction': 'adults_only',
                'severity': 'moderate',
                'prescription_required': False
            },
            {
                'name': 'Metformin',
                'generic_name': 'Metformin HCl',
                'dosage_form': 'Tablet',
                'strength': '500mg',
                'description': 'Diabetes medication to control blood sugar',
                'usage_instructions': 'Take with meals to reduce stomach upset.',
                'dosage_adult': '500mg twice daily, may increase gradually',
                'dosage_children': 'As prescribed by pediatric endocrinologist',
                'side_effects': 'Nausea, diarrhea, stomach upset, metallic taste',
                'warnings': 'Monitor kidney function. Stop before contrast procedures.',
                'contraindications': 'Severe kidney disease, diabetic ketoacidosis',
                'age_restriction': 'adults_only',
                'severity': 'strong',
                'prescription_required': True
            }
        ]
        
        cursor = self.connection.cursor()
        
        for medicine in sample_medicines:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO medicines 
                    (name, generic_name, dosage_form, strength, description, usage_instructions,
                     dosage_adult, dosage_children, side_effects, warnings, contraindications,
                     age_restriction, severity, prescription_required)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    medicine['name'], medicine['generic_name'], medicine['dosage_form'],
                    medicine['strength'], medicine['description'], medicine['usage_instructions'],
                    medicine['dosage_adult'], medicine['dosage_children'], medicine['side_effects'],
                    medicine['warnings'], medicine['contraindications'], medicine['age_restriction'],
                    medicine['severity'], medicine['prescription_required']
                ))
            except sqlite3.Error as e:
                print(f"Error inserting medicine {medicine['name']}: {e}")
        
        self.connection.commit()
    
    def search_medicine(self, search_term):
        """Search for medicine by name or generic name."""
        if not self.connect():
            return None
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM medicines 
                WHERE LOWER(name) LIKE LOWER(?) OR LOWER(generic_name) LIKE LOWER(?)
                ORDER BY 
                    CASE 
                        WHEN LOWER(name) = LOWER(?) THEN 1
                        WHEN LOWER(name) LIKE LOWER(?) THEN 2
                        WHEN LOWER(generic_name) LIKE LOWER(?) THEN 3
                        ELSE 4
                    END
            ''', (f'%{search_term}%', f'%{search_term}%', search_term, f'{search_term}%', f'{search_term}%'))
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
        
        except sqlite3.Error as e:
            print(f"Medicine search error: {e}")
            return None
        finally:
            self.disconnect()
    
    def get_medicine_by_id(self, medicine_id):
        """Get medicine details by ID."""
        if not self.connect():
            return None
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM medicines WHERE id = ?', (medicine_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        
        except sqlite3.Error as e:
            print(f"Get medicine error: {e}")
            return None
        finally:
            self.disconnect()
    
    def add_user_medicine(self, medicine_id, user_dosage, frequency, start_date, end_date=None, notes=""):
        """Add a medicine to user's current medicine list."""
        if not self.connect():
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO user_medicines 
                (medicine_id, user_dosage, frequency, start_date, end_date, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (medicine_id, user_dosage, frequency, start_date, end_date, notes))
            
            self.connection.commit()
            return cursor.lastrowid
        
        except sqlite3.Error as e:
            print(f"Add user medicine error: {e}")
            return False
        finally:
            self.disconnect()
    
    def get_active_user_medicines(self):
        """Get all active medicines for the user."""
        if not self.connect():
            return []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT um.*, m.name, m.generic_name, m.dosage_form, m.strength
                FROM user_medicines um
                JOIN medicines m ON um.medicine_id = m.id
                WHERE um.active = 1
                ORDER BY um.created_at DESC
            ''')
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
        
        except sqlite3.Error as e:
            print(f"Get active medicines error: {e}")
            return []
        finally:
            self.disconnect()
    
    def add_reminder(self, user_medicine_id, reminder_time, frequency):
        """Add a reminder for a user's medicine."""
        if not self.connect():
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO reminders (user_medicine_id, reminder_time, frequency)
                VALUES (?, ?, ?)
            ''', (user_medicine_id, reminder_time, frequency))
            
            self.connection.commit()
            return cursor.lastrowid
        
        except sqlite3.Error as e:
            print(f"Add reminder error: {e}")
            return False
        finally:
            self.disconnect()
    
    def get_active_reminders(self):
        """Get all active reminders."""
        if not self.connect():
            return []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT r.*, um.user_dosage, m.name as medicine_name
                FROM reminders r
                JOIN user_medicines um ON r.user_medicine_id = um.id
                JOIN medicines m ON um.medicine_id = m.id
                WHERE r.active = 1 AND um.active = 1
                ORDER BY r.reminder_time
            ''')
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
        
        except sqlite3.Error as e:
            print(f"Get reminders error: {e}")
            return []
        finally:
            self.disconnect()
    
    def log_medicine_taken(self, user_medicine_id, scheduled_time, status="taken", notes=""):
        """Log when a medicine was taken."""
        if not self.connect():
            return False
        
        try:
            if isinstance(scheduled_time, (datetime.datetime, datetime.date)):
                scheduled_time = scheduled_time.isoformat()
            taken_at = datetime.datetime.now().isoformat()
            
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO medicine_logs 
                (user_medicine_id, taken_at, scheduled_time, status, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_medicine_id, taken_at, scheduled_time, status, notes))
            
            self.connection.commit()
            return True
        
        except sqlite3.Error as e:
            print(f"Log medicine error: {e}")
            return False
        finally:
            self.disconnect()
    
    def save_ocr_result(self, image_path, extracted_text, recognized_medicine, confidence_score):
        """Save OCR processing result to history."""
        if not self.connect():
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO ocr_history 
                (image_path, extracted_text, recognized_medicine, confidence_score)
                VALUES (?, ?, ?, ?)
            ''', (image_path, extracted_text, recognized_medicine, confidence_score))
            
            self.connection.commit()
            return True
        
        except sqlite3.Error as e:
            print(f"Save OCR result error: {e}")
            return False
        finally:
            self.disconnect()
    
    def get_medicine_history(self, days=30):
        """Get medicine taking history for the last specified days."""
        if not self.connect():
            return []
        
        try:
            cursor = self.connection.cursor()
            cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
            
            cursor.execute('''
                SELECT ml.*, um.user_dosage, m.name as medicine_name
                FROM medicine_logs ml
                JOIN user_medicines um ON ml.user_medicine_id = um.id
                JOIN medicines m ON um.medicine_id = m.id
                WHERE ml.taken_at >= ?
                ORDER BY ml.taken_at DESC
            ''', (cutoff_date,))
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
        
        except sqlite3.Error as e:
            print(f"Get medicine history error: {e}")
            return []
        finally:
            self.disconnect()