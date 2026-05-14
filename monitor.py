import time
import json
import os
import re
import threading
import pyttsx3
from pynput import mouse, keyboard


try:
    import win32gui
    import win32process
    import psutil
except Exception as e:
    raise RuntimeError("This monitor requires pywin32 and psutil (Windows). Install them before running.\n" + str(e))

from tts import TTS
from natural_tts import NaturalTTS
from db import log_usage

CONFIG_PATH = 'config.json'

class FocusMonitor:
    def __init__(self, config_path=CONFIG_PATH):
        self.config_path = config_path
        self._load_config()
        # self.tts = TTS()
        self.tts = NaturalTTS()
        self._last_alert_ts = 0

        self.last_title = ""
        self.last_proc_name = ""
        self.last_activity = time.time()
        

        # Start listeners
        self.mouse_listener = mouse.Listener(on_move=self._on_activity, on_click=self._on_activity)
        self.keyboard_listener = keyboard.Listener(on_press=self._on_activity)
        self.mouse_listener.start()
        self.keyboard_listener.start()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Missing {self.config_path}. Create one based on the example in this project.")
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.cfg = json.load(f)
        # normalize allowed apps to lowercase
        self.allowed_apps = [a.lower() for a in self.cfg.get('allowed_apps', [])]
        self.allowed_site_keywords = self.cfg.get('allowed_site_keywords', [])
        self.site_keywords_not_allowed = self.cfg.get('site_keywords_not_allowed', [])
        self.interval = self.cfg.get('check_interval_seconds', 3)
        self.snooze_seconds = self.cfg.get('snooze_seconds', 60)
        self.min_time_before_alert = self.cfg.get('min_time_before_alert_seconds', 5)
        self.name = self.cfg.get('name', 'User')
        self.voice_template = self.cfg.get('block_voice', 'Focus!')
        self.idle_limit = self.cfg.get('idle_limit', 60)

    def _get_active_window_info(self):
        hwnd = win32gui.GetForegroundWindow()
        if hwnd == 0:
            return None, None, None
        title = win32gui.GetWindowText(hwnd)
        try:
            tid, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc = psutil.Process(pid)
            proc_name = proc.name()
        except Exception:
            proc_name = None
            pid = None
            print(proc_name, title, pid)
        return proc_name, title, pid

    def _is_allowed(self, proc_name, title):
        # Check title for not allowed site keywords
        for kw in self.site_keywords_not_allowed:
            if kw.lower() in title.lower():
                return False, 'blocked'
        # Check app
        proc_name_l = (proc_name or '').lower()
        for allowed in self.allowed_apps:
            if allowed in proc_name_l:
                return True, 'app_allowed'
        # Check title for allowed site keywords (browser tabs include page title)
        for kw in self.allowed_site_keywords:
            if kw.lower() in title.lower():
                return True, 'site_allowed'
        
        return False, 'blocked'
    def _get_context_message(self, proc_name, title):
        name = proc_name.lower() if proc_name else ""
        title = title.lower() if title else ""

        if "youtube" in title or "youtube" in name:
            return "You just opened YouTube. Let's not waste time watching videos, Danial."
        elif "facebook" in title or "instagram" in title or "twitter" in title:
            return "Social media detected. Remember your goals and stay focused."
        elif "explorer" in name:
            return "Browsing files again? Keep your workspace tidy and stay on track."
        elif "spotify" in name or "music" in title:
            return "Music is fine, but don’t get lost in the rhythm."
        elif "chrome" in name or "edge" in name:
            return "You opened your browser. Only search what helps your work, okay?"
        elif "vscode" in name or "code" in title:
            return "Nice! You’re coding. Keep the focus strong, Danial!"
        elif "powerpoint" in title or "word" in title or "excel" in title:
            return "Working on documents? Stay productive and avoid distractions."
        else:
            return f"You opened {proc_name or title}. Stay mindful."

    def _speak_alert(self, proc_name, title):
        text = self.voice_template.replace('{name}', self.name)
        # Add contextual message
        context = self._get_context_message(proc_name, title)
        message = f"{text} {context}"
        # print(f"[TTS] {message}")
        self.tts.say(text + ' ' + context)

    def _alarm(self, text):
        self.tts.say(text)

    def _on_activity(self, *args):
        self.last_activity = time.time()

    # def _get_active_window_process(self):
    #     try:
    #         hwnd = win32gui.GetForegroundWindow()
    #         _, pid = win32process.GetWindowThreadProcessId(hwnd)
    #         process = psutil.Process(pid)
    #         return process.name(), win32gui.GetWindowText(hwnd)
    #     except Exception:
    #         return None, None

    def _monitor_idle(self):
        last_alert_time = 0
        # print(" Idle Monitor started... for ",self.idle_limit," sec")
        while True:
            time.sleep(5)
            idle_time = time.time() - self.last_activity

            # Debug print to see what’s happening
            # print(f"[IDLE] idle_time={idle_time:.1f}s")

            if idle_time > self.idle_limit and (time.time() - last_alert_time > self.idle_limit):
                self._alarm("You've been inactive for a while. Please move or focus back.")
                last_alert_time = time.time()

    # def _monitor_active_window(self):
    #     while True:
    #         proc_name, title = self._get_active_window_process()
    #         if not proc_name:
    #             time.sleep(1)
    #             continue

    #         if proc_name != self.last_proc_name and proc_name.strip() != "":
    #             self.last_proc_name = proc_name
    #             # if "code" in proc_name.lower():
    #             #     msg = "Coding mode on — let's build something amazing!"
    #             # elif "chrome" in proc_name.lower():
    #             #     msg = "Browsing again? Stay focused!"
    #             if "youtube" in proc_name.lower():
    #                 msg = "YouTube detected!"
    #             else:
    #                 msg = "Switch detected."
    #             # self._alarm(f"{msg} You opened {proc_name or title}")
    #         time.sleep(2)


    def start(self):
        print('FocusMonitor started — press Ctrl+C to stop')
        last_change_ts = time.time()
        last_proc = None
        last_title = None
        focus_period_start = time.time()


        # Start both monitoring threads
        threading.Thread(target=self._monitor_idle, daemon=True).start()
        # threading.Thread(target=self._monitor_active_window, daemon=True).start()

        # Keep the main thread alive
        while True:
            try:
                proc_name, title, pid = self._get_active_window_info()
                if proc_name != last_proc or title != last_title:
                    last_change_ts = time.time()
                    last_proc = proc_name
                    last_title = title

                # if the active window has been active for at least min_time_before_alert
                active_duration = time.time() - last_change_ts
                allowed, reason = self._is_allowed(proc_name, title)
                # print(f"[{time.strftime('%H:%M:%S')}] Active: {proc_name} | {title} | Allowed: {allowed} | Duration: {active_duration:.1f}s")
                if not allowed and active_duration >= self.min_time_before_alert:
                    # avoid alerting too frequently (snooze)
                    if time.time() - self._last_alert_ts > self.snooze_seconds:
                        # print(f"[ALERT] {proc_name} | {title}")
                        self._speak_alert(proc_name, title)
                        log_usage(proc_name or 'unknown', title or 'no-title', 'distraction')
                        self._last_alert_ts = time.time()
                else:
                    # log allowed activity as well (only when window changes)
                    if active_duration < 2 and (proc_name or title):
                        log_usage(proc_name or 'unknown', title or 'no-title', reason)

                time.sleep(self.interval)
            except KeyboardInterrupt:
                print('Stopping FocusMonitor...')
                break
            except Exception as e:
                # don't crash — log and continue
                print('Monitor error:', e)
                time.sleep(self.interval)


    