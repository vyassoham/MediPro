#!/usr/bin/env python3
"""
Smart Medicine Reminder & Tracker
Created by Soham Vyas

A comprehensive Python desktop application for medicine recognition, tracking, and reminder system
using OCR and medical knowledge base.
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui import MedicineTrackerGUI
from database import MedicineDatabase
from reminder_system import ReminderSystem


def main():
    """Main entry point for the Smart Medicine Reminder & Tracker application."""
    try:
        # Initialize the database
        database = MedicineDatabase()
        database.initialize_database()
        
        # Create the main application window
        root = tk.Tk()
        
        # Initialize the reminder system with GUI callback
        reminder_system = ReminderSystem(database)
        
        # Create the main application
        app = MedicineTrackerGUI(root, database, reminder_system)
        
        # Start the reminder system
        reminder_system.start()
        
        # Start the GUI main loop
        app.run()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()