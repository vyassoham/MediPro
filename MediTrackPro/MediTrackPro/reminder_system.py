"""
Reminder System module for Smart Medicine Reminder & Tracker
Handles scheduling and notification of medicine reminders
"""

import datetime
import threading
import time
import queue
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from plyer import notification
import tkinter as tk
from tkinter import messagebox
from config import REMINDER_SOUND_ENABLED, REMINDER_POPUP_DURATION, REMINDER_SNOOZE_DURATION


class ReminderSystem:
    """Manages medicine reminders and notifications."""
    
    def __init__(self, database, gui_callback=None):
        """
        Initialize reminder system.
        
        Args:
            database: Database instance for accessing reminder data
            gui_callback: Callback function to show UI reminders safely
        """
        self.database = database
        self.scheduler = BackgroundScheduler()
        self.active_reminders = {}
        self.notification_windows = {}
        self.gui_callback = gui_callback
        self.reminder_queue = queue.Queue()
        
    def start(self):
        """Start the reminder scheduler."""
        try:
            self.scheduler.start()
            self._load_reminders_from_database()
            print("Reminder system started successfully")
        except Exception as e:
            print(f"Failed to start reminder system: {e}")
    
    def stop(self):
        """Stop the reminder scheduler."""
        try:
            self.scheduler.shutdown()
            print("Reminder system stopped")
        except Exception as e:
            print(f"Error stopping reminder system: {e}")
    
    def _load_reminders_from_database(self):
        """Load active reminders from database and schedule them."""
        try:
            reminders = self.database.get_active_reminders()
            
            for reminder in reminders:
                self._schedule_reminder(reminder)
                
        except Exception as e:
            print(f"Error loading reminders from database: {e}")
    
    def _schedule_reminder(self, reminder):
        """
        Schedule a single reminder.
        
        Args:
            reminder (dict): Reminder data from database
        """
        try:
            reminder_id = reminder['id']
            reminder_time = reminder['reminder_time']
            frequency = reminder['frequency']
            medicine_name = reminder['medicine_name']
            user_dosage = reminder['user_dosage']
            
            # Parse reminder time
            time_parts = reminder_time.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            
            # Create trigger based on frequency
            if frequency == 'daily':
                trigger = CronTrigger(hour=hour, minute=minute)
            elif frequency == 'weekly':
                # Default to once a week on the same day
                trigger = CronTrigger(day_of_week=0, hour=hour, minute=minute)
            elif frequency == 'twice_daily':
                # Schedule for morning and evening
                self.scheduler.add_job(
                    func=self._trigger_reminder,
                    trigger=CronTrigger(hour=8, minute=0),
                    args=[reminder],
                    id=f"reminder_{reminder_id}_morning",
                    replace_existing=True
                )
                self.scheduler.add_job(
                    func=self._trigger_reminder,
                    trigger=CronTrigger(hour=20, minute=0),
                    args=[reminder],
                    id=f"reminder_{reminder_id}_evening",
                    replace_existing=True
                )
                return
            elif frequency == 'three_times_daily':
                # Schedule for morning, afternoon, and evening
                for time_slot, slot_hour in [('morning', 8), ('afternoon', 14), ('evening', 20)]:
                    self.scheduler.add_job(
                        func=self._trigger_reminder,
                        trigger=CronTrigger(hour=slot_hour, minute=0),
                        args=[reminder],
                        id=f"reminder_{reminder_id}_{time_slot}",
                        replace_existing=True
                    )
                return
            else:
                trigger = CronTrigger(hour=hour, minute=minute)
            
            # Add job to scheduler
            job_id = f"reminder_{reminder_id}"
            self.scheduler.add_job(
                func=self._trigger_reminder,
                trigger=trigger,
                args=[reminder],
                id=job_id,
                replace_existing=True
            )
            
            self.active_reminders[reminder_id] = {
                'job_id': job_id,
                'reminder_data': reminder
            }
            
            print(f"Scheduled reminder for {medicine_name} at {reminder_time}")
            
        except Exception as e:
            print(f"Error scheduling reminder {reminder.get('id', 'unknown')}: {e}")
    
    def _trigger_reminder(self, reminder):
        """
        Trigger a medicine reminder notification.
        
        Args:
            reminder (dict): Reminder data
        """
        try:
            medicine_name = reminder['medicine_name']
            user_dosage = reminder['user_dosage']
            current_time = datetime.datetime.now()
            
            # Create notification message
            message = f"Time to take your medicine!\n\n"
            message += f"Medicine: {medicine_name}\n"
            message += f"Dosage: {user_dosage}\n"
            message += f"Time: {current_time.strftime('%H:%M')}"
            
            # Show desktop notification (thread-safe)
            self._show_desktop_notification(medicine_name, user_dosage)
            
            # Queue reminder data for UI thread (thread-safe)
            reminder_data = {
                'reminder': reminder,
                'message': message,
                'scheduled_time': current_time
            }
            self.reminder_queue.put(reminder_data)
            print(f"Reminder queued for UI thread: {medicine_name}")
            
            print(f"Reminder triggered for {medicine_name} at {current_time.strftime('%H:%M')}")
            
        except Exception as e:
            print(f"Error triggering reminder: {e}")
    
    def _show_desktop_notification(self, medicine_name, dosage):
        """
        Show desktop notification using plyer.
        
        Args:
            medicine_name (str): Name of the medicine
            dosage (str): Dosage information
        """
        try:
            notification.notify(
                title="Medicine Reminder",
                message=f"Time to take {medicine_name}\nDosage: {dosage}",
                app_name="Smart Medicine Tracker",
                timeout=REMINDER_POPUP_DURATION
            )
        except Exception as e:
            print(f"Error showing desktop notification: {e}")
    
    def _show_reminder_popup(self, reminder, message, scheduled_time):
        """
        Show reminder popup window.
        
        Args:
            reminder (dict): Reminder data
            message (str): Reminder message
            scheduled_time (datetime): Scheduled time for the reminder
        """
        try:
            # Create popup window
            popup = tk.Toplevel()
            popup.title("Medicine Reminder")
            popup.geometry("400x300")
            popup.resizable(False, False)
            
            # Make window stay on top
            popup.attributes("-topmost", True)
            
            # Center window on screen
            popup.update_idletasks()
            x = (popup.winfo_screenwidth() // 2) - (400 // 2)
            y = (popup.winfo_screenheight() // 2) - (300 // 2)
            popup.geometry(f"400x300+{x}+{y}")
            
            # Message label
            msg_label = tk.Label(
                popup, 
                text=message, 
                font=("Arial", 12), 
                justify=tk.LEFT,
                padx=20,
                pady=20
            )
            msg_label.pack(expand=True, fill=tk.BOTH)
            
            # Button frame
            button_frame = tk.Frame(popup)
            button_frame.pack(pady=10)
            
            # Taken button
            taken_btn = tk.Button(
                button_frame,
                text="✓ Taken",
                font=("Arial", 10, "bold"),
                bg="#4CAF50",
                fg="white",
                width=10,
                command=lambda: self._mark_as_taken(reminder, scheduled_time, popup)
            )
            taken_btn.pack(side=tk.LEFT, padx=5)
            
            # Snooze button
            snooze_btn = tk.Button(
                button_frame,
                text="⏰ Snooze",
                font=("Arial", 10),
                bg="#FF9800",
                fg="white",
                width=10,
                command=lambda: self._snooze_reminder(reminder, scheduled_time, popup)
            )
            snooze_btn.pack(side=tk.LEFT, padx=5)
            
            # Skip button
            skip_btn = tk.Button(
                button_frame,
                text="✗ Skip",
                font=("Arial", 10),
                bg="#F44336",
                fg="white",
                width=10,
                command=lambda: self._skip_reminder(reminder, scheduled_time, popup)
            )
            skip_btn.pack(side=tk.LEFT, padx=5)
            
            # Store reference to prevent garbage collection
            reminder_id = reminder['id']
            self.notification_windows[reminder_id] = popup
            
            # Auto-close after timeout
            popup.after(REMINDER_POPUP_DURATION * 1000, lambda: self._auto_close_popup(popup, reminder_id))
            
        except Exception as e:
            print(f"Error showing reminder popup: {e}")
    
    def _mark_as_taken(self, reminder, scheduled_time, popup):
        """
        Mark medicine as taken and log it.
        
        Args:
            reminder (dict): Reminder data
            scheduled_time (datetime): Scheduled time
            popup (tk.Toplevel): Popup window to close
        """
        try:
            user_medicine_id = reminder['user_medicine_id']
            
            # Log medicine as taken
            success = self.database.log_medicine_taken(
                user_medicine_id, scheduled_time, "taken", "Marked as taken via reminder"
            )
            
            if success:
                print(f"Medicine {reminder['medicine_name']} marked as taken")
            else:
                print(f"Failed to log medicine {reminder['medicine_name']} as taken")
            
            # Close popup
            self._close_popup(popup, reminder['id'])
            
        except Exception as e:
            print(f"Error marking medicine as taken: {e}")
    
    def _snooze_reminder(self, reminder, scheduled_time, popup):
        """
        Snooze the reminder for a specified duration.
        
        Args:
            reminder (dict): Reminder data
            scheduled_time (datetime): Original scheduled time
            popup (tk.Toplevel): Popup window to close
        """
        try:
            # Close current popup
            self._close_popup(popup, reminder['id'])
            
            # Schedule snooze reminder
            snooze_time = datetime.datetime.now() + datetime.timedelta(minutes=REMINDER_SNOOZE_DURATION)
            
            job_id = f"snooze_{reminder['id']}_{int(time.time())}"
            self.scheduler.add_job(
                func=self._trigger_reminder,
                trigger='date',
                run_date=snooze_time,
                args=[reminder],
                id=job_id
            )
            
            print(f"Reminder snoozed for {REMINDER_SNOOZE_DURATION} minutes")
            
        except Exception as e:
            print(f"Error snoozing reminder: {e}")
    
    def _skip_reminder(self, reminder, scheduled_time, popup):
        """
        Skip the current reminder and log it.
        
        Args:
            reminder (dict): Reminder data
            scheduled_time (datetime): Scheduled time
            popup (tk.Toplevel): Popup window to close
        """
        try:
            user_medicine_id = reminder['user_medicine_id']
            
            # Log medicine as skipped
            success = self.database.log_medicine_taken(
                user_medicine_id, scheduled_time, "skipped", "Skipped via reminder popup"
            )
            
            if success:
                print(f"Medicine {reminder['medicine_name']} marked as skipped")
            else:
                print(f"Failed to log medicine {reminder['medicine_name']} as skipped")
            
            # Close popup
            self._close_popup(popup, reminder['id'])
            
        except Exception as e:
            print(f"Error skipping reminder: {e}")
    
    def _auto_close_popup(self, popup, reminder_id):
        """
        Auto-close popup after timeout.
        
        Args:
            popup (tk.Toplevel): Popup window
            reminder_id (int): Reminder ID
        """
        try:
            if popup.winfo_exists():
                popup.destroy()
                if reminder_id in self.notification_windows:
                    del self.notification_windows[reminder_id]
        except Exception:
            pass
    
    def _close_popup(self, popup, reminder_id):
        """
        Close popup window and clean up references.
        
        Args:
            popup (tk.Toplevel): Popup window
            reminder_id (int): Reminder ID
        """
        try:
            popup.destroy()
            if reminder_id in self.notification_windows:
                del self.notification_windows[reminder_id]
        except Exception as e:
            print(f"Error closing popup: {e}")
    
    def add_reminder(self, user_medicine_id, reminder_time, frequency):
        """
        Add a new reminder and schedule it.
        
        Args:
            user_medicine_id (int): User medicine ID
            reminder_time (str): Time in HH:MM format
            frequency (str): Frequency (daily, weekly, etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add to database
            reminder_id = self.database.add_reminder(user_medicine_id, reminder_time, frequency)
            
            if reminder_id:
                # Get full reminder data
                reminders = self.database.get_active_reminders()
                for reminder in reminders:
                    if reminder['id'] == reminder_id:
                        self._schedule_reminder(reminder)
                        return True
            
            return False
            
        except Exception as e:
            print(f"Error adding reminder: {e}")
            return False
    
    def remove_reminder(self, reminder_id):
        """
        Remove a reminder from the scheduler.
        
        Args:
            reminder_id (int): Reminder ID to remove
        """
        try:
            if reminder_id in self.active_reminders:
                job_id = self.active_reminders[reminder_id]['job_id']
                
                # Remove from scheduler
                try:
                    self.scheduler.remove_job(job_id)
                except:
                    pass  # Job might not exist
                
                # Remove from active reminders
                del self.active_reminders[reminder_id]
                
                print(f"Reminder {reminder_id} removed")
                
        except Exception as e:
            print(f"Error removing reminder {reminder_id}: {e}")
    
    def get_next_reminders(self, hours=24):
        """
        Get upcoming reminders within specified hours.
        
        Args:
            hours (int): Number of hours to look ahead
            
        Returns:
            list: List of upcoming reminders
        """
        try:
            upcoming = []
            now = datetime.datetime.now()
            cutoff = now + datetime.timedelta(hours=hours)
            
            for job in self.scheduler.get_jobs():
                if job.next_run_time and now <= job.next_run_time <= cutoff:
                    # Extract reminder info from job args
                    if job.args and len(job.args) > 0:
                        reminder = job.args[0]
                        upcoming.append({
                            'id': reminder['id'],
                            'medicine_name': reminder['medicine_name'],
                            'user_dosage': reminder['user_dosage'],
                            'next_run': job.next_run_time,
                            'job_id': job.id
                        })
            
            # Sort by next run time
            upcoming.sort(key=lambda x: x['next_run'])
            return upcoming
            
        except Exception as e:
            print(f"Error getting next reminders: {e}")
            return []