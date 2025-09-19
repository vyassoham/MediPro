# MediPro
MediPro is a smart desktop app that provides complete details about any medicine, including composition, dosage, side effects, and interactions. With an easy interface and offline access, it empowers patients, students, and healthcare professionals to make safe, informed decisions about medicines anytime

💊 Smart Medicine Reminder & Tracker
📌 Project Overview

The Smart Medicine Reminder & Tracker is a Python-based desktop application designed to solve one of the most common real-life problems: forgetting to take medicines on time and not knowing proper details about prescribed medicines. Millions of people, especially elderly patients or those with multiple prescriptions, face challenges in remembering the correct dosage, timing, and even the purpose of each medicine they are taking. This project bridges that gap by acting like a personal medical assistant.

The system combines OCR (Optical Character Recognition), a medicine knowledge base, and a reminder system into one simple, user-friendly interface. A patient or caregiver can simply take a photo of a medicine strip or prescription, upload it to the app, and instantly get:

The name of the medicine

Dosage instructions (when and how to take it)

Age restrictions (safe for children, adults, elderly, etc.)

Side effects and warnings

Whether it is OTC (Over-the-Counter) or Prescription Only

Severity classification (mild/common, moderate, strong drug)

Once the medicine is recognized, the app allows users to set reminders that notify them at the right times, track when they have taken their medicine, and maintain a history log for better health management.

🎯 Problem Statement

Forgetfulness and lack of medical awareness are two major contributors to poor medication adherence. According to studies, around 50% of patients do not take medicines as prescribed, which can lead to severe complications, prolonged recovery, or even life-threatening consequences.

Additionally, people often:

Do not understand what their prescribed medicine is for.

Do not remember the right time and dosage.

Accidentally take incompatible medicines together.

Lack awareness about potential side effects.

While there are apps available in the market, many are not open-source, rely on complex mobile installations, or lack local/offline functionality. Our project aims to provide a free, open-source, cross-platform solution that anyone can run on their computer.

🔑 Key Features

Image-Based Medicine Recognition

Upload a photo of a medicine strip or prescription.

The app uses OCR (pytesseract + OpenCV) to extract text.

Recognizes medicine name and dosage printed on the packaging.

Medicine Knowledge Base

Integrated with DailyMed / DrugBank / RxNorm APIs (or custom SQLite database).

Provides detailed information about each medicine: usage, dosage, age suitability, side effects, and severity.

Helps patients understand their treatment better.

Smart Reminders

Users can set daily/weekly reminders for medicines.

Notifications pop up at the right time.

Option to snooze or mark as taken.

Tracking & Logs

Maintains history of when medicines were taken.

Can export logs for sharing with doctors or caregivers.

User-Friendly Interface

Built with Tkinter for simplicity and accessibility.

Clear buttons for uploading medicine images, checking info, and setting reminders.

Displays images, extracted text, and medicine details in a neat dashboard.

Future Enhancements (Planned)

Integration with voice input for elderly users.

Mobile companion app using the same backend.

AI-based pill recognition by shape and color (not just text).

Multi-user support for families.

🛠️ How It Works

Step 1: Upload/Click Image
The user uploads an image of their medicine strip or prescription.

Step 2: OCR Processing

The image is preprocessed (converted to grayscale, threshold applied).

pytesseract extracts text from the image.

Example output: "Paracetamol 500mg Tablet".

Step 3: Knowledge Base Lookup

The extracted medicine name is searched in the local SQLite database.

If not found, the app can query online sources like DailyMed or DrugBank.

Step 4: Display Medicine Info
The app shows all relevant details:

Dosage: “1 tablet twice a day after food”

Side Effects: “Drowsiness, nausea, mild headache”

Age Restriction: “Not suitable for children under 6 years”

Severity: “Mild – safe OTC drug”

Step 5: Set Reminders

User can set reminders (e.g., “8 AM and 8 PM daily”).

Notifications alert the user at those times.

Step 6: Track History

When the user marks a reminder as “Taken,” it is logged.

Doctors or caregivers can review the medication adherence report.

🌍 Real-Life Impact

This project is not just a coding exercise but a real-life problem solver. It can:

Help elderly patients who forget medicines often.

Assist busy professionals who take multiple prescriptions.

Support caregivers in monitoring medication schedules.

Spread medical awareness by explaining drugs in simple language.

By being open-source, it empowers developers and researchers worldwide to contribute, enhance, and localize the solution for different regions and languages.

🚀 Tech Stack

Python 3

Tkinter → UI

pytesseract + OpenCV → OCR & image processing

SQLite → Local medicine database

APScheduler / schedule → Reminder scheduling

Requests → API integration with external knowledge bases
