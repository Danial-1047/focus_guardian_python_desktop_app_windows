import sqlite3
import datetime
import threading

DB_FILENAME = 'focusguardian.db'

_lock = threading.Lock()

def init_db():
    with _lock:
        conn = sqlite3.connect(DB_FILENAME)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT,
                app TEXT,
                title TEXT,
                reason TEXT
            )
        ''')
        conn.commit()
        conn.close()

def log_usage(app, title, reason):
    ts = datetime.datetime.utcnow().isoformat()
    with _lock:
        conn = sqlite3.connect(DB_FILENAME)
        c = conn.cursor()
        c.execute('INSERT INTO usage_log (ts, app, title, reason) VALUES (?, ?, ?, ?)',
                  (ts, app, title, reason))
        conn.commit()
        conn.close()

def get_today_summary():
    today = datetime.date.today().isoformat()
    with _lock:
        conn = sqlite3.connect(DB_FILENAME)
        c = conn.cursor()
        c.execute("SELECT COUNT(*), COUNT(DISTINCT app) FROM usage_log WHERE date(ts)=?", (today,))
        row = c.fetchone()
        conn.close()
        if row:
            return {'total_events': row[0], 'distinct_apps': row[1]}
        return {'total_events': 0, 'distinct_apps': 0}

