
import json
import os
import threading
import time

from monitor import FocusMonitor
from db import init_db, get_today_summary

import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import sys

import tkinter as tk
from tkinter import messagebox

def show_config_message(config):
    win = tk.Tk()
    win.title("FocusGuardian Config")
    win.geometry("400x300")

    text = tk.Text(win, wrap="word")
    text.insert("1.0", json.dumps(config, indent=4))
    text.config(state="disabled")
    text.pack(expand=True, fill="both")

    def on_close():
        win.destroy()  # Proper close
    win.protocol("WM_DELETE_WINDOW", on_close)

    win.mainloop()


# ---------- Load Config ----------
def resource_path(relative_path):
    """
    Get absolute path to resource — works in development and PyInstaller bundle.
    """
    if hasattr(sys, '_MEIPASS'):
        # Running from the PyInstaller temporary folder
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # Running from source or after installation
        return os.path.join(os.path.abspath("."), relative_path)

def load_config():
    """Load editable config.json next to EXE or fallback to bundled one"""
    # Path next to executable (editable)
    exe_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
    external_config = os.path.join(exe_dir, "config.json")

    if os.path.exists(external_config):
        config_path = external_config
    else:
        # Fallback to bundled config inside PyInstaller package
        config_path = resource_path("config.json")

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

# -------- Show config in Tkinter --------
def show_config_window():
    config = load_config()
    win = tk.Tk()
    win.title("FocusGuardian Config")
    win.geometry("400x300")

    text = tk.Text(win, wrap="word")
    text.insert("1.0", json.dumps(config, indent=4))
    text.config(state="disabled")
    text.pack(expand=True, fill="both")

    def on_close():
        win.destroy()  # Proper close
    win.protocol("WM_DELETE_WINDOW", on_close)

    win.mainloop()

# -------- Create tray icon --------
def create_tray():
    def on_show_config(icon, item):
        threading.Thread(target=show_config_window).start()

    def on_quit(icon, item):
        icon.stop()
        os._exit(0)

    image_path = resource_path("focus.ico")
    image = Image.open(image_path)

    # image = Image.new('RGB', (64, 64), (100, 200, 255))

    
    menu = pystray.Menu(
        pystray.MenuItem("Show Config", on_show_config),
        pystray.MenuItem("Quit", on_quit)
    )

    icon = pystray.Icon("FocusGuardian", image, "FocusGuardian", menu)
    icon.run()


def main():
    # initialize DB
    init_db()

    tray_thread = threading.Thread(target=create_tray, daemon=True)
    tray_thread.start()
      # --- Step 2: Find config.json ---
    exe_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
    cfg_path = os.path.join(exe_dir, 'config.json')

    # Fallback to bundled config (inside EXE) if missing
    if not os.path.exists(cfg_path):
        bundled_cfg = resource_path('config.json')
        if os.path.exists(bundled_cfg):
            cfg_path = bundled_cfg
        else:
            print('❌ Missing config.json. Create one next to the EXE or main.py (see README).')
            return
    # start monitor
    monitor = FocusMonitor(cfg_path)    

    # run monitor in main thread (so Ctrl+C works nicely)
    try:
        monitor.start()
    except Exception as e:
        print('Fatal error:', e)
    finally:
        # on exit, print today's summary
        summary = get_today_summary()
        print(f"Today's usage summary: {summary['total_events']} events across {summary['distinct_apps']} apps.")


if __name__ == '__main__':
    main()
    
    




# FocusGuardian — Voice-enabled Focus Assistant (Windows)
# -----------------------------------------------------
# A small Python desktop app that monitors the active window, detects
# distractions (apps or websites), speaks an alarm, and logs usage to SQLite.
#
# What this deliverable contains (single-file project layout inside this document):
# - requirements.txt       -> required Python packages
# - config.json            -> customizable allowed/block lists and settings
# - main.py                -> entrypoint (starts monitor & TTS)
# - monitor.py             -> active window detection and logic
# - tts.py                 -> text-to-speech wrapper
# - db.py                  -> simple SQLite logger and daily summary
# - README.md              -> run instructions
#
# NOTES & DESIGN CHOICES
# - This version targets Windows (uses pywin32 to read active window title).
# - Browser URLs are inferred from window title (Chrome/Edge/Firefox show tab title).
#   This avoids requiring special browser permissions / remote debugging.
# - When a distraction is detected, FocusGuardian will speak a configurable message
#   and create a log entry. It will not forcibly close apps.
# - All dependencies used are free and open-source.
#
# -----------------------------------------------------------------------------

