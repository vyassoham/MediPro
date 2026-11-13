"""
GUI module for Smart Medicine Reminder & Tracker
Tkinter-based desktop interface for the medicine tracking application
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import os
import datetime
import threading
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    SUPPORTED_IMAGE_FORMATS, UPLOADS_DIR, MEDICINE_SEVERITY, AGE_RESTRICTIONS
)
from ocr_processor import OCRProcessor


class MedicineTrackerGUI:
    """Main GUI class for the Smart Medicine Reminder & Tracker application."""
    
    def __init__(self, root, database, reminder_system):
        """
        Initialize the GUI.
        
        Args:
            root (tk.Tk): Root window
            database: Database instance
            reminder_system: Reminder system instance
        """
        self.root = root
        self.database = database
        self.reminder_system = reminder_system
        self.ocr_processor = OCRProcessor()
        
        # GUI state variables
        self.current_image_path = None
        self.current_medicine_data = None
        self.selected_medicine_id = None
        
        self._setup_window()
        self._create_widgets()
        self._load_initial_data()
        
        # Set up reminder checking
        self._check_pending_reminders()
    
    def _setup_window(self):
        """Configure the main window."""
        self.root.title("Smart Medicine Reminder & Tracker - Created by Soham Vyas")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (WINDOW_WIDTH // 2)
        y = (self.root.winfo_screenheight() // 2) - (WINDOW_HEIGHT // 2)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
        
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
    
    def _create_widgets(self):
        """Create and layout all GUI widgets."""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self._create_scan_tab()
        self._create_medicines_tab()
        self._create_reminders_tab()
        self._create_history_tab()
    
    def _create_scan_tab(self):
        """Create the medicine scanning tab."""
        scan_frame = ttk.Frame(self.notebook)
        self.notebook.add(scan_frame, text="Scan Medicine")
        
        # Main container with two columns
        main_container = ttk.Frame(scan_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left column - Image upload and display
        left_frame = ttk.LabelFrame(main_container, text="Image Upload & Processing", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Upload button
        upload_btn = ttk.Button(
            left_frame,
            text="📷 Upload Medicine Image",
            command=self._upload_image,
            style="Accent.TButton"
        )
        upload_btn.pack(pady=5)
        
        # Image display
        self.image_label = tk.Label(left_frame, text="No image uploaded", bg="lightgray", height=15)
        self.image_label.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # OCR results
        ocr_frame = ttk.LabelFrame(left_frame, text="Extracted Text", padding=5)
        ocr_frame.pack(fill=tk.X, pady=5)
        
        self.ocr_text = scrolledtext.ScrolledText(ocr_frame, height=6, wrap=tk.WORD)
        self.ocr_text.pack(fill=tk.BOTH, expand=True)
        
        # Process button
        process_btn = ttk.Button(
            left_frame,
            text="🔍 Process Image",
            command=self._process_image,
            state=tk.DISABLED
        )
        process_btn.pack(pady=5)
        self.process_btn = process_btn
        
        # Right column - Medicine information
        right_frame = ttk.LabelFrame(main_container, text="Medicine Information", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Medicine search
        search_frame = ttk.Frame(right_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Search Medicine:").pack(anchor=tk.W)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(fill=tk.X, pady=2)
        self.search_entry.bind('<KeyRelease>', self._on_search_change)
        
        search_btn = ttk.Button(search_frame, text="Search", command=self._search_medicine)
        search_btn.pack(pady=2)
        
        # Medicine details
        details_frame = ttk.LabelFrame(right_frame, text="Medicine Details", padding=5)
        details_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.medicine_details = scrolledtext.ScrolledText(details_frame, height=15, wrap=tk.WORD, state=tk.DISABLED)
        self.medicine_details.pack(fill=tk.BOTH, expand=True)
        
        # Add to tracker button
        add_btn = ttk.Button(
            right_frame,
            text="➕ Add to My Medicines",
            command=self._show_add_medicine_dialog,
            state=tk.DISABLED
        )
        add_btn.pack(pady=5)
        self.add_medicine_btn = add_btn
    
    def _create_medicines_tab(self):
        """Create the current medicines tab."""
        medicines_frame = ttk.Frame(self.notebook)
        self.notebook.add(medicines_frame, text="My Medicines")
        
        # Toolbar
        toolbar = ttk.Frame(medicines_frame)
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(toolbar, text="🔄 Refresh", command=self._refresh_medicines).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="➕ Add Medicine", command=self._show_add_medicine_dialog).pack(side=tk.LEFT, padx=5)
        
        # Medicines list
        list_frame = ttk.LabelFrame(medicines_frame, text="Current Medicines", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview for medicines
        columns = ("Name", "Dosage", "Frequency", "Start Date", "Status")
        self.medicines_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.medicines_tree.heading(col, text=col)
            self.medicines_tree.column(col, width=120)
        
        # Scrollbar for treeview
        medicines_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.medicines_tree.yview)
        self.medicines_tree.configure(yscrollcommand=medicines_scrollbar.set)
        
        self.medicines_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        medicines_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click event
        self.medicines_tree.bind("<Double-1>", self._on_medicine_double_click)
    
    def _create_reminders_tab(self):
        """Create the reminders management tab."""
        reminders_frame = ttk.Frame(self.notebook)
        self.notebook.add(reminders_frame, text="Reminders")
        
        # Split into two sections
        main_container = ttk.Frame(reminders_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left - Current reminders
        left_frame = ttk.LabelFrame(main_container, text="Active Reminders", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Reminders list
        reminder_columns = ("Medicine", "Time", "Frequency", "Next Due")
        self.reminders_tree = ttk.Treeview(left_frame, columns=reminder_columns, show="headings", height=12)
        
        for col in reminder_columns:
            self.reminders_tree.heading(col, text=col)
            self.reminders_tree.column(col, width=100)
        
        reminders_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.reminders_tree.yview)
        self.reminders_tree.configure(yscrollcommand=reminders_scrollbar.set)
        
        self.reminders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        reminders_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Reminder buttons
        reminder_btn_frame = ttk.Frame(left_frame)
        reminder_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(reminder_btn_frame, text="🔄 Refresh", command=self._refresh_reminders).pack(side=tk.LEFT, padx=5)
        ttk.Button(reminder_btn_frame, text="❌ Delete", command=self._delete_reminder).pack(side=tk.LEFT, padx=5)
        
        # Right - Add new reminder
        right_frame = ttk.LabelFrame(main_container, text="Add New Reminder", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # Medicine selection
        ttk.Label(right_frame, text="Select Medicine:").pack(anchor=tk.W, pady=2)
        self.reminder_medicine_combo = ttk.Combobox(right_frame, state="readonly", width=25)
        self.reminder_medicine_combo.pack(fill=tk.X, pady=2)
        
        # Time selection
        ttk.Label(right_frame, text="Reminder Time:").pack(anchor=tk.W, pady=(10, 2))
        time_frame = ttk.Frame(right_frame)
        time_frame.pack(fill=tk.X, pady=2)
        
        self.hour_var = tk.StringVar(value="08")
        self.minute_var = tk.StringVar(value="00")
        
        hour_combo = ttk.Combobox(time_frame, textvariable=self.hour_var, values=[f"{i:02d}" for i in range(24)], width=3, state="readonly")
        hour_combo.pack(side=tk.LEFT)
        
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT, padx=2)
        
        minute_combo = ttk.Combobox(time_frame, textvariable=self.minute_var, values=[f"{i:02d}" for i in range(0, 60, 15)], width=3, state="readonly")
        minute_combo.pack(side=tk.LEFT)
        
        # Frequency selection
        ttk.Label(right_frame, text="Frequency:").pack(anchor=tk.W, pady=(10, 2))
        self.frequency_var = tk.StringVar(value="daily")
        frequency_combo = ttk.Combobox(
            right_frame,
            textvariable=self.frequency_var,
            values=["daily", "twice_daily", "three_times_daily", "weekly"],
            state="readonly",
            width=25
        )
        frequency_combo.pack(fill=tk.X, pady=2)
        
        # Add reminder button
        add_reminder_btn = ttk.Button(
            right_frame,
            text="➕ Add Reminder",
            command=self._add_reminder
        )
        add_reminder_btn.pack(pady=20)
        
        # Upcoming reminders
        upcoming_frame = ttk.LabelFrame(right_frame, text="Next 24 Hours", padding=5)
        upcoming_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.upcoming_text = scrolledtext.ScrolledText(upcoming_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        self.upcoming_text.pack(fill=tk.BOTH, expand=True)
    
    def _create_history_tab(self):
        """Create the medicine history tab."""
        history_frame = ttk.Frame(self.notebook)
        self.notebook.add(history_frame, text="History")
        
        # Toolbar
        toolbar = ttk.Frame(history_frame)
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(toolbar, text="🔄 Refresh", command=self._refresh_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="📊 Export", command=self._export_history).pack(side=tk.LEFT, padx=5)
        
        # Date filter
        filter_frame = ttk.Frame(toolbar)
        filter_frame.pack(side=tk.RIGHT)
        
        ttk.Label(filter_frame, text="Days:").pack(side=tk.LEFT, padx=2)
        self.history_days_var = tk.StringVar(value="30")
        days_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.history_days_var,
            values=["7", "30", "90", "365"],
            width=5,
            state="readonly"
        )
        days_combo.pack(side=tk.LEFT, padx=2)
        days_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_history())
        
        # History list
        list_frame = ttk.LabelFrame(history_frame, text="Medicine History", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview for history
        history_columns = ("Date/Time", "Medicine", "Dosage", "Status", "Notes")
        self.history_tree = ttk.Treeview(list_frame, columns=history_columns, show="headings", height=20)
        
        for col in history_columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=120)
        
        # Scrollbar for history
        history_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _load_initial_data(self):
        """Load initial data into the GUI."""
        self._refresh_medicines()
        self._refresh_reminders()
        self._refresh_history()
        self._update_reminder_medicine_combo()
    
    def _upload_image(self):
        """Handle image upload."""
        file_types = [
            ("Image files", " ".join(f"*{ext}" for ext in SUPPORTED_IMAGE_FORMATS)),
            ("All files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Select Medicine Image",
            filetypes=file_types
        )
        
        if file_path:
            # Validate image
            is_valid, error_msg = self.ocr_processor.validate_image_file(file_path)
            if not is_valid:
                messagebox.showerror("Invalid Image", error_msg)
                return
            
            # Copy to uploads directory
            import shutil
            filename = os.path.basename(file_path)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{timestamp}_{filename}"
            new_path = os.path.join(UPLOADS_DIR, new_filename)
            
            try:
                shutil.copy2(file_path, new_path)
                self.current_image_path = new_path
                
                # Display image
                self._display_image(new_path)
                
                # Enable process button
                self.process_btn.config(state=tk.NORMAL)
                
                # Clear previous results
                self.ocr_text.delete(1.0, tk.END)
                self._clear_medicine_details()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy image: {str(e)}")
    
    def _display_image(self, image_path):
        """Display the uploaded image in the GUI."""
        try:
            # Open and resize image
            with Image.open(image_path) as img:
                # Calculate size to fit in label while maintaining aspect ratio
                label_width = 400
                label_height = 300
                
                img_width, img_height = img.size
                ratio = min(label_width / img_width, label_height / img_height)
                
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(resized_img)
                
                # Update label
                self.image_label.config(image=photo, text="")
                self.image_label.image = photo  # Keep a reference
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display image: {str(e)}")
    
    def _process_image(self):
        """Process the uploaded image with OCR."""
        if not self.current_image_path:
            messagebox.showwarning("No Image", "Please upload an image first.")
            return
        
        # Show processing message
        self.ocr_text.delete(1.0, tk.END)
        self.ocr_text.insert(tk.END, "Processing image... Please wait.")
        self.root.update()
        
        # Process in background thread
        thread = threading.Thread(target=self._process_image_thread)
        thread.daemon = True
        thread.start()
    
    def _process_image_thread(self):
        """Process image in background thread."""
        try:
            # Process image
            results = self.ocr_processor.process_medicine_image(self.current_image_path, self.database)
            
            # Update GUI in main thread
            self.root.after(0, self._update_ocr_results, results)
            
        except Exception as e:
            error_msg = f"Error processing image: {str(e)}"
            self.root.after(0, self._show_processing_error, error_msg)
    
    def _update_ocr_results(self, results):
        """Update GUI with OCR results."""
        # Update OCR text
        self.ocr_text.delete(1.0, tk.END)
        
        if results['processing_successful']:
            extracted_text = results['extracted_text']
            potential_medicines = results['potential_medicines']
            
            self.ocr_text.insert(tk.END, f"Extracted Text:\n{extracted_text}\n\n")
            self.ocr_text.insert(tk.END, f"OCR Confidence: {results['ocr_confidence']:.1f}%\n\n")
            
            if potential_medicines:
                self.ocr_text.insert(tk.END, "Potential Medicines Found:\n")
                for med in potential_medicines:
                    self.ocr_text.insert(tk.END, f"• {med['name']} (Confidence: {med['confidence']:.2f})\n")
                
                # Auto-search for the best match
                best_match = potential_medicines[0]['name']
                self.search_entry.delete(0, tk.END)
                self.search_entry.insert(0, best_match)
                self._search_medicine()
            else:
                if not self.ocr_processor.is_tesseract_available():
                    self.ocr_text.insert(tk.END, "⚠️ Note: Tesseract OCR was not found on your system PATH.\nPlease install Tesseract OCR to enable automatic medicine packaging text extraction, or use manual search below.")
                else:
                    self.ocr_text.insert(tk.END, "No medicines recognized. Try manual search.")
        else:
            error_msg = results.get('error', 'Unknown error')
            self.ocr_text.insert(tk.END, f"Processing failed: {error_msg}")
    
    def _show_processing_error(self, error_msg):
        """Show processing error in GUI."""
        self.ocr_text.delete(1.0, tk.END)
        self.ocr_text.insert(tk.END, error_msg)
        messagebox.showerror("Processing Error", error_msg)
    
    def _search_medicine(self):
        """Search for medicine in database."""
        search_term = self.search_entry.get().strip()
        if not search_term:
            messagebox.showwarning("No Search Term", "Please enter a medicine name to search.")
            return
        
        results = self.database.search_medicine(search_term)
        if results:
            # Show first result
            medicine = results[0]
            self._display_medicine_details(medicine)
            self.current_medicine_data = medicine
            self.selected_medicine_id = medicine['id']
            self.add_medicine_btn.config(state=tk.NORMAL)
        else:
            self._clear_medicine_details()
            self.add_medicine_btn.config(state=tk.DISABLED)
            messagebox.showinfo("No Results", f"No medicine found matching '{search_term}'.")
    
    def _display_medicine_details(self, medicine):
        """Display medicine details in the text widget."""
        self.medicine_details.config(state=tk.NORMAL)
        self.medicine_details.delete(1.0, tk.END)
        
        details = f"""Medicine Name: {medicine['name']}
Generic Name: {medicine['generic_name']}
Form: {medicine['dosage_form']} - {medicine['strength']}

Description:
{medicine['description']}

Usage Instructions:
{medicine['usage_instructions']}

Dosage:
• Adults: {medicine['dosage_adult']}
• Children: {medicine['dosage_children']}

Side Effects:
{medicine['side_effects']}

Warnings:
{medicine['warnings']}

Age Restriction: {AGE_RESTRICTIONS.get(medicine['age_restriction'], medicine['age_restriction'])}
Severity: {MEDICINE_SEVERITY.get(medicine['severity'], medicine['severity'])}
Prescription Required: {'Yes' if medicine['prescription_required'] else 'No'}
"""
        
        self.medicine_details.insert(tk.END, details)
        self.medicine_details.config(state=tk.DISABLED)
    
    def _clear_medicine_details(self):
        """Clear medicine details display."""
        self.medicine_details.config(state=tk.NORMAL)
        self.medicine_details.delete(1.0, tk.END)
        self.medicine_details.insert(tk.END, "No medicine selected.")
        self.medicine_details.config(state=tk.DISABLED)
        self.current_medicine_data = None
        self.selected_medicine_id = None
    
    def _on_search_change(self, event):
        """Handle search entry changes."""
        # Auto-search after a brief delay
        self.root.after(500, self._search_medicine)
    
    def _show_add_medicine_dialog(self):
        """Show dialog to add medicine to user's list."""
        if not self.selected_medicine_id:
            messagebox.showwarning("No Medicine Selected", "Please select a medicine first.")
            return
        
        dialog = AddMedicineDialog(self.root, self.current_medicine_data, self.database, self.reminder_system)
        if dialog.result:
            self._refresh_medicines()
            self._refresh_reminders()
            self._update_reminder_medicine_combo()
            messagebox.showinfo("Success", "Medicine added successfully!")
    
    def _refresh_medicines(self):
        """Refresh the medicines list."""
        # Clear current items
        for item in self.medicines_tree.get_children():
            self.medicines_tree.delete(item)
        
        # Load medicines from database
        medicines = self.database.get_active_user_medicines()
        
        for medicine in medicines:
            start_date = datetime.datetime.strptime(medicine['start_date'], '%Y-%m-%d').strftime('%Y-%m-%d')
            status = "Active" if medicine['active'] else "Inactive"
            
            self.medicines_tree.insert("", tk.END, values=(
                medicine['name'],
                medicine['user_dosage'],
                medicine['frequency'],
                start_date,
                status
            ))
    
    def _refresh_reminders(self):
        """Refresh the reminders list."""
        # Clear current items
        for item in self.reminders_tree.get_children():
            self.reminders_tree.delete(item)
        
        # Load reminders from database
        reminders = self.database.get_active_reminders()
        
        for reminder in reminders:
            # Get next reminder time
            next_reminders = self.reminder_system.get_next_reminders(24)
            next_due = "N/A"
            for next_rem in next_reminders:
                if next_rem['id'] == reminder['id']:
                    next_due = next_rem['next_run'].strftime('%H:%M')
                    break
            
            self.reminders_tree.insert("", tk.END, values=(
                reminder['medicine_name'],
                reminder['reminder_time'],
                reminder['frequency'],
                next_due
            ))
        
        # Update upcoming reminders
        self._update_upcoming_reminders()
    
    def _refresh_history(self):
        """Refresh the medicine history."""
        # Clear current items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Get number of days
        try:
            days = int(self.history_days_var.get())
        except ValueError:
            days = 30
        
        # Load history from database
        history = self.database.get_medicine_history(days)
        
        for entry in history:
            taken_at = datetime.datetime.strptime(entry['taken_at'], '%Y-%m-%d %H:%M:%S.%f')
            date_str = taken_at.strftime('%Y-%m-%d %H:%M')
            
            self.history_tree.insert("", tk.END, values=(
                date_str,
                entry['medicine_name'],
                entry['user_dosage'],
                entry['status'].title(),
                entry['notes'] or ""
            ))
    
    def _update_reminder_medicine_combo(self):
        """Update the reminder medicine combobox."""
        medicines = self.database.get_active_user_medicines()
        medicine_options = [f"{med['name']} - {med['user_dosage']}" for med in medicines]
        
        self.reminder_medicine_combo['values'] = medicine_options
        if medicine_options:
            self.reminder_medicine_combo.current(0)
    
    def _add_reminder(self):
        """Add a new reminder."""
        if not self.reminder_medicine_combo.get():
            messagebox.showwarning("No Medicine", "Please select a medicine for the reminder.")
            return
        
        # Get medicine ID
        medicine_name = self.reminder_medicine_combo.get().split(' - ')[0]
        medicines = self.database.get_active_user_medicines()
        user_medicine_id = None
        
        for med in medicines:
            if med['name'] == medicine_name:
                user_medicine_id = med['id']
                break
        
        if not user_medicine_id:
            messagebox.showerror("Error", "Selected medicine not found.")
            return
        
        # Get reminder details
        reminder_time = f"{self.hour_var.get()}:{self.minute_var.get()}"
        frequency = self.frequency_var.get()
        
        # Add reminder
        success = self.reminder_system.add_reminder(user_medicine_id, reminder_time, frequency)
        
        if success:
            messagebox.showinfo("Success", "Reminder added successfully!")
            self._refresh_reminders()
        else:
            messagebox.showerror("Error", "Failed to add reminder.")
    
    def _delete_reminder(self):
        """Delete selected reminder."""
        selection = self.reminders_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a reminder to delete.")
            return
        
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this reminder?"):
            # Implementation would require getting reminder ID from selection
            messagebox.showinfo("Info", "Reminder deletion feature to be implemented.")
    
    def _update_upcoming_reminders(self):
        """Update the upcoming reminders display."""
        self.upcoming_text.config(state=tk.NORMAL)
        self.upcoming_text.delete(1.0, tk.END)
        
        upcoming = self.reminder_system.get_next_reminders(24)
        
        if upcoming:
            self.upcoming_text.insert(tk.END, "Next 24 hours:\n\n")
            for reminder in upcoming:
                time_str = reminder['next_run'].strftime('%H:%M')
                self.upcoming_text.insert(tk.END, f"• {time_str} - {reminder['medicine_name']}\n")
        else:
            self.upcoming_text.insert(tk.END, "No upcoming reminders in the next 24 hours.")
        
        self.upcoming_text.config(state=tk.DISABLED)
    
    def _export_history(self):
        """Export medicine history to CSV."""
        try:
            import csv
            
            file_path = filedialog.asksaveasfilename(
                title="Export History",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if file_path:
                days = int(self.history_days_var.get())
                history = self.database.get_medicine_history(days)
                
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Date/Time', 'Medicine', 'Dosage', 'Status', 'Notes'])
                    
                    for entry in history:
                        taken_at = datetime.datetime.strptime(entry['taken_at'], '%Y-%m-%d %H:%M:%S.%f')
                        date_str = taken_at.strftime('%Y-%m-%d %H:%M')
                        
                        writer.writerow([
                            date_str,
                            entry['medicine_name'],
                            entry['user_dosage'],
                            entry['status'].title(),
                            entry['notes'] or ""
                        ])
                
                messagebox.showinfo("Success", f"History exported to {file_path}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export history: {str(e)}")
    
    def _on_medicine_double_click(self, event):
        """Handle double-click on medicine in list."""
        selection = self.medicines_tree.selection()
        if selection:
            # Implementation for editing medicine details
            messagebox.showinfo("Info", "Medicine editing feature to be implemented.")
    
    def _check_pending_reminders(self):
        """Check for pending reminders from thread-safe queue and show UI popups."""
        try:
            # Process all queued reminders (non-blocking)
            while True:
                try:
                    reminder_data = self.reminder_system.reminder_queue.get_nowait()
                    print(f"Processing reminder from queue: {reminder_data['reminder']['medicine_name']}")
                    self._show_reminder_popup_safe(
                        reminder_data['reminder'],
                        reminder_data['message'],
                        reminder_data['scheduled_time']
                    )
                    self.reminder_system.reminder_queue.task_done()
                except Exception:
                    # No more items in queue
                    break
        except Exception as e:
            print(f"Error checking pending reminders: {e}")
        
        # Schedule next check
        self.root.after(1000, self._check_pending_reminders)
    
    def _show_reminder_popup_safe(self, reminder, message, scheduled_time):
        """Thread-safe version of showing reminder popup."""
        try:
            # Create popup window
            popup = tk.Toplevel(self.root)
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
                command=lambda: self._mark_as_taken_safe(reminder, scheduled_time, popup)
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
                command=lambda: self._snooze_reminder_safe(reminder, scheduled_time, popup)
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
                command=lambda: self._skip_reminder_safe(reminder, scheduled_time, popup)
            )
            skip_btn.pack(side=tk.LEFT, padx=5)
            
            # Auto-close after timeout
            popup.after(30000, lambda: self._auto_close_popup_safe(popup))
            
        except Exception as e:
            print(f"Error showing reminder popup: {e}")
    
    def _mark_as_taken_safe(self, reminder, scheduled_time, popup):
        """Thread-safe version of marking medicine as taken."""
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
            popup.destroy()
            
        except Exception as e:
            print(f"Error marking medicine as taken: {e}")
    
    def _snooze_reminder_safe(self, reminder, scheduled_time, popup):
        """Thread-safe version of snoozing reminder."""
        try:
            # Close current popup
            popup.destroy()
            
            # Add snooze reminder back to pending list
            snooze_time = datetime.datetime.now() + datetime.timedelta(minutes=10)
            snooze_reminder = {
                'reminder': reminder,
                'message': f"Snooze reminder: {reminder['medicine_name']}",
                'scheduled_time': snooze_time
            }
            
            # Schedule snooze check
            self.root.after(10 * 60 * 1000, lambda: self._add_snooze_reminder(snooze_reminder))
            
            print(f"Reminder snoozed for 10 minutes")
            
        except Exception as e:
            print(f"Error snoozing reminder: {e}")
    
    def _add_snooze_reminder(self, snooze_reminder):
        """Add snoozed reminder back to queue."""
        self.reminder_system.reminder_queue.put(snooze_reminder)
    
    def _skip_reminder_safe(self, reminder, scheduled_time, popup):
        """Thread-safe version of skipping reminder."""
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
            popup.destroy()
            
        except Exception as e:
            print(f"Error skipping reminder: {e}")
    
    def _auto_close_popup_safe(self, popup):
        """Thread-safe version of auto-closing popup."""
        try:
            if popup.winfo_exists():
                popup.destroy()
        except Exception:
            pass

    def run(self):
        """Start the GUI main loop."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit()
    
    def quit(self):
        """Clean shutdown of the application."""
        try:
            self.reminder_system.stop()
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            print(f"Error during shutdown: {e}")


class AddMedicineDialog:
    """Dialog for adding a medicine to user's list."""
    
    def __init__(self, parent, medicine_data, database, reminder_system):
        """
        Initialize the add medicine dialog.
        
        Args:
            parent: Parent window
            medicine_data (dict): Medicine information
            database: Database instance
            reminder_system: Reminder system instance
        """
        self.medicine_data = medicine_data
        self.database = database
        self.reminder_system = reminder_system
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Medicine to Tracker")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (300 // 2)
        self.dialog.geometry(f"400x300+{x}+{y}")
        
        self._create_widgets()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def _create_widgets(self):
        """Create dialog widgets."""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Medicine name
        ttk.Label(main_frame, text=f"Medicine: {self.medicine_data['name']}", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)
        
        # Dosage
        ttk.Label(main_frame, text="Your Dosage:").pack(anchor=tk.W, pady=(10, 2))
        self.dosage_entry = ttk.Entry(main_frame, width=30)
        self.dosage_entry.pack(fill=tk.X, pady=2)
        self.dosage_entry.insert(0, self.medicine_data.get('dosage_adult', ''))
        
        # Frequency
        ttk.Label(main_frame, text="Frequency:").pack(anchor=tk.W, pady=(10, 2))
        self.frequency_var = tk.StringVar(value="daily")
        frequency_combo = ttk.Combobox(
            main_frame,
            textvariable=self.frequency_var,
            values=["daily", "twice_daily", "three_times_daily", "weekly", "as_needed"],
            state="readonly"
        )
        frequency_combo.pack(fill=tk.X, pady=2)
        
        # Start date
        ttk.Label(main_frame, text="Start Date:").pack(anchor=tk.W, pady=(10, 2))
        self.start_date_var = tk.StringVar(value=datetime.date.today().strftime('%Y-%m-%d'))
        start_date_entry = ttk.Entry(main_frame, textvariable=self.start_date_var)
        start_date_entry.pack(fill=tk.X, pady=2)
        
        # Notes
        ttk.Label(main_frame, text="Notes:").pack(anchor=tk.W, pady=(10, 2))
        self.notes_text = tk.Text(main_frame, height=4, wrap=tk.WORD)
        self.notes_text.pack(fill=tk.X, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="Add Medicine", command=self._add_medicine).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.LEFT, padx=5)
    
    def _add_medicine(self):
        """Add the medicine to user's list."""
        try:
            dosage = self.dosage_entry.get().strip()
            frequency = self.frequency_var.get()
            start_date = self.start_date_var.get()
            notes = self.notes_text.get(1.0, tk.END).strip()
            
            if not dosage:
                messagebox.showwarning("Missing Information", "Please enter dosage information.")
                return
            
            # Add to database
            user_medicine_id = self.database.add_user_medicine(
                self.medicine_data['id'],
                dosage,
                frequency,
                start_date,
                notes=notes
            )
            
            if user_medicine_id:
                self.result = user_medicine_id
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to add medicine to tracker.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add medicine: {str(e)}")
    
    def _cancel(self):
        """Cancel the dialog."""
        self.dialog.destroy()