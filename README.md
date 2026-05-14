FocusGuardian — Voice-enabled Focus Assistant (Windows)

Overview
--------
A small Python app that monitors the active window and speaks an alert when a distraction
(app or website) is detected. All events are logged into a local SQLite database (focusguardian.db).

Prerequisites
-------------
- Windows 10/11
- Python 3.9+ (64-bit recommended)
- pip

Installation
------------
1. Create a new folder and save the files from this project there (main.py, monitor.py, tts.py, db.py, config.json).
2. Create the `requirements.txt` file with the package list shown at the top of this document.
3. Open an elevated command prompt (optional) and run:

   python -m pip install --upgrade pip
   pip install -r requirements.txt

4. Prepare `config.json` by copying the example provided above and editing `allowed_apps` and
   `allowed_site_keywords` to match what you consider productive.

Usage
-----
Run the app:

    python main.py

The app will start monitoring the active window and will speak an alert when it detects
an unallowed app/tab that remains active for `min_time_before_alert_seconds` seconds.

Customization
-------------
- `allowed_apps`: list of substrings of process names that are allowed (e.g., "vscode", "chrome").
- `allowed_site_keywords`: list of keywords that can appear in browser tab titles that should be
   considered allowed (e.g., "ChatGPT", "Google").
- `block_voice`: TTS message template. Use `{name}` placeholder.
- `snooze_seconds`: minimum seconds between spoken alerts to avoid repetition.
- `check_interval_seconds`: how often the monitor checks the active window.

How it detects browser pages
----------------------------
This first version reads the active window title (Chrome/Edge/Firefox display the tab's title).
So if a tab has the word "YouTube" in the title it will be treated as a distraction unless
"YouTube" is added to `allowed_site_keywords`.

Privacy & Safety
----------------
- This app runs locally and stores a small local SQLite database. No data is sent to the cloud.
- If you want to add an option to ignore certain windows, edit `config.json`.
