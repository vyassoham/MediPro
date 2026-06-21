import sqlite3
import datetime
import pytest

def test_database_initialization(db):
    """Verify that tables are initialized and populated with sample data."""
    assert db.connect()
    
    # Check tables exist
    cursor = db.connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    assert "medicines" in tables
    assert "user_medicines" in tables
    assert "reminders" in tables
    assert "medicine_logs" in tables
    assert "ocr_history" in tables
    
    # Verify sample data populated
    cursor.execute("SELECT count(*) FROM medicines")
    count = cursor.fetchone()[0]
    assert count > 0
    
    db.disconnect()

def test_search_medicine(db):
    """Verify searching for medicines works with exact and partial matches."""
    # Exact match search
    results = db.search_medicine("Paracetamol")
    assert results is not None
    assert len(results) >= 1
    assert results[0]['name'] == "Paracetamol"
    assert results[0]['generic_name'] == "Acetaminophen"
    
    # Case-insensitive partial search
    results = db.search_medicine("para")
    assert results is not None
    assert any(m['name'] == "Paracetamol" for m in results)
    
    # Non-existent search
    results = db.search_medicine("XYZUnknownMed")
    assert results == []

def test_user_medicine_lifecycle(db):
    """Verify adding, retrieving and tracking user's active medicines."""
    # Find Paracetamol ID
    results = db.search_medicine("Paracetamol")
    med_id = results[0]['id']
    
    # Add to user list
    start_date = datetime.date.today().strftime('%Y-%m-%d')
    user_med_id = db.add_user_medicine(
        medicine_id=med_id,
        user_dosage="500mg",
        frequency="daily",
        start_date=start_date,
        notes="Take after lunch"
    )
    
    assert user_med_id is not False
    assert isinstance(user_med_id, int)
    
    # Retrieve active user medicines
    active_meds = db.get_active_user_medicines()
    assert len(active_meds) >= 1
    assert active_meds[0]['id'] == user_med_id
    assert active_meds[0]['name'] == "Paracetamol"
    assert active_meds[0]['user_dosage'] == "500mg"
    assert active_meds[0]['notes'] == "Take after lunch"

def test_reminders(db):
    """Verify adding and retrieving active reminders."""
    results = db.search_medicine("Ibuprofen")
    med_id = results[0]['id']
    
    user_med_id = db.add_user_medicine(
        medicine_id=med_id,
        user_dosage="400mg",
        frequency="twice_daily",
        start_date=datetime.date.today().strftime('%Y-%m-%d')
    )
    
    # Add reminders
    r1_id = db.add_reminder(user_med_id, "08:00", "twice_daily")
    r2_id = db.add_reminder(user_med_id, "20:00", "twice_daily")
    
    assert r1_id is not False
    assert r2_id is not False
    
    # Retrieve reminders
    active_reminders = db.get_active_reminders()
    assert len(active_reminders) >= 2
    
    med_names = [r['medicine_name'] for r in active_reminders]
    assert "Ibuprofen" in med_names
    
    times = [r['reminder_time'] for r in active_reminders]
    assert "08:00" in times
    assert "20:00" in times

def test_medicine_logs_and_history(db):
    """Verify logging medicine usage and retrieving history."""
    results = db.search_medicine("Amoxicillin")
    med_id = results[0]['id']
    
    user_med_id = db.add_user_medicine(
        medicine_id=med_id,
        user_dosage="250mg",
        frequency="three_times_daily",
        start_date=datetime.date.today().strftime('%Y-%m-%d')
    )
    
    scheduled_time = datetime.datetime.now() - datetime.timedelta(hours=2)
    
    # Log taken
    assert db.log_medicine_taken(user_med_id, scheduled_time, "taken", "Felt better")
    # Log skipped
    assert db.log_medicine_taken(user_med_id, scheduled_time, "skipped", "Forgot")
    
    # Get history
    history = db.get_medicine_history(days=1)
    assert len(history) >= 2
    assert history[0]['medicine_name'] == "Amoxicillin"
    assert history[0]['status'] in ["taken", "skipped"]

def test_ocr_history_logging(db):
    """Verify logging of OCR operations in database."""
    success = db.save_ocr_result(
        image_path="/path/to/img.png",
        extracted_text="Aspirin 75mg",
        recognized_medicine="Aspirin",
        confidence_score=92.5
    )
    assert success
    
    # Directly query the database to verify insert
    assert db.connect()
    cursor = db.connection.cursor()
    cursor.execute("SELECT * FROM ocr_history WHERE recognized_medicine = 'Aspirin'")
    row = cursor.fetchone()
    assert row is not None
    assert row['extracted_text'] == "Aspirin 75mg"
    assert row['confidence_score'] == 92.5
    db.disconnect()
