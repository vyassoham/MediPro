import datetime
import pytest
from unittest.mock import MagicMock, patch
from reminder_system import ReminderSystem

@pytest.fixture
def mock_scheduler():
    """Fixture to mock BackgroundScheduler."""
    with patch('reminder_system.BackgroundScheduler') as mock_class:
        mock_sched = MagicMock()
        mock_class.return_value = mock_sched
        yield mock_sched

def test_reminder_system_start_stop(db, mock_scheduler):
    """Verify reminder system starts scheduler and stops it properly."""
    system = ReminderSystem(database=db)
    
    # Mock load reminders method
    system._load_reminders_from_database = MagicMock()
    
    system.start()
    mock_scheduler.start.assert_called_once()
    system._load_reminders_from_database.assert_called_once()
    
    system.stop()
    mock_scheduler.shutdown.assert_called_once()

def test_add_and_schedule_reminder(db, mock_scheduler):
    """Verify adding a reminder inserts into database and schedules it."""
    # Prepare active user medicine in database
    med_results = db.search_medicine("Paracetamol")
    med_id = med_results[0]['id']
    user_med_id = db.add_user_medicine(
        medicine_id=med_id,
        user_dosage="500mg",
        frequency="daily",
        start_date=datetime.date.today().strftime('%Y-%m-%d')
    )
    
    system = ReminderSystem(database=db)
    
    # Add a daily reminder at 08:30
    success = system.add_reminder(user_med_id, "08:30", "daily")
    assert success
    
    # Verify job added to scheduler
    mock_scheduler.add_job.assert_called_once()
    args, kwargs = mock_scheduler.add_job.call_args
    
    assert kwargs['id'].startswith("reminder_")
    assert kwargs['replace_existing'] is True
    # The callback function should be system._trigger_reminder
    assert kwargs['func'] == system._trigger_reminder

def test_trigger_reminder(db, mock_scheduler):
    """Verify triggering a reminder queues the data and sends notification."""
    system = ReminderSystem(database=db)
    
    reminder_data = {
        'id': 1,
        'user_medicine_id': 5,
        'reminder_time': "08:30",
        'frequency': "daily",
        'medicine_name': "Paracetamol",
        'user_dosage': "500mg"
    }
    
    # Trigger the reminder
    system._trigger_reminder(reminder_data)
    
    # Verify notification was sent (mock_notification runs automatically via conftest)
    from plyer import notification
    notification.notify.assert_called_once_with(
        title="Medicine Reminder",
        message="Time to take Paracetamol\nDosage: 500mg",
        app_name="Smart Medicine Tracker",
        timeout=30
    )
    
    # Verify reminder is queued for the UI thread
    assert not system.reminder_queue.empty()
    queued = system.reminder_queue.get()
    assert queued['reminder'] == reminder_data
    assert "Time to take your medicine!" in queued['message']
    assert "Paracetamol" in queued['message']

def test_remove_reminder(db, mock_scheduler):
    """Verify removing a reminder updates scheduler and internal tracking."""
    system = ReminderSystem(database=db)
    
    # Track an active reminder
    system.active_reminders[12] = {
        'job_id': 'reminder_12',
        'reminder_data': {'id': 12}
    }
    
    system.remove_reminder(12)
    
    mock_scheduler.remove_job.assert_called_once_with('reminder_12')
    assert 12 not in system.active_reminders

def test_different_frequencies(db, mock_scheduler):
    """Verify different frequency configurations schedule the correct jobs."""
    system = ReminderSystem(database=db)
    
    # 1. Daily frequency
    rem_daily = {
        'id': 1,
        'reminder_time': "08:00",
        'frequency': "daily",
        'medicine_name': "Paracetamol",
        'user_dosage': "500mg"
    }
    system._schedule_reminder(rem_daily)
    assert mock_scheduler.add_job.call_count == 1
    
    # 2. Twice daily frequency (schedules two separate jobs)
    mock_scheduler.reset_mock()
    rem_twice = {
        'id': 2,
        'reminder_time': "08:00",
        'frequency': "twice_daily",
        'medicine_name': "Paracetamol",
        'user_dosage': "500mg"
    }
    system._schedule_reminder(rem_twice)
    assert mock_scheduler.add_job.call_count == 2
    
    # 3. Three times daily frequency (schedules three separate jobs)
    mock_scheduler.reset_mock()
    rem_thrice = {
        'id': 3,
        'reminder_time': "08:00",
        'frequency': "three_times_daily",
        'medicine_name': "Paracetamol",
        'user_dosage': "500mg"
    }
    system._schedule_reminder(rem_thrice)
    assert mock_scheduler.add_job.call_count == 3
