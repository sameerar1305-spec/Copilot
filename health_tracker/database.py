"""
SQLite Database Manager for Mental Health & Medical Tracker
Handles all data persistence for user health records, phone usage logs,
mental health assessments, and medical ailment tracking.
"""

import sqlite3
import os
from datetime import datetime, date


DB_PATH = os.path.join(os.path.expanduser("~"), ".health_tracker", "health_data.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize all database tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # User profile
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Daily mental health check-in
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mental_health_checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            checkin_date TEXT NOT NULL,
            mood_score INTEGER NOT NULL,          -- 1-10 scale
            anxiety_level INTEGER NOT NULL,       -- 1-10 scale
            stress_level INTEGER NOT NULL,        -- 1-10 scale
            sleep_hours REAL,
            sleep_quality INTEGER,                -- 1-10 scale
            energy_level INTEGER,                 -- 1-10 scale
            social_interaction INTEGER,           -- 1-10 scale
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phone usage sessions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS phone_usage_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            usage_date TEXT NOT NULL,
            app_category TEXT NOT NULL,           -- social_media, gaming, work, etc.
            duration_minutes INTEGER NOT NULL,
            session_start TEXT,
            session_end TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Medical ailments log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medical_ailments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            log_date TEXT NOT NULL,
            ailment_type TEXT NOT NULL,           -- headache, eye_strain, neck_pain, etc.
            severity INTEGER NOT NULL,            -- 1-10 scale
            duration_minutes INTEGER,
            possible_trigger TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Daily phone usage summary (aggregated)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_usage_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            summary_date TEXT NOT NULL UNIQUE,
            total_screen_time_minutes INTEGER DEFAULT 0,
            pickups_count INTEGER DEFAULT 0,
            longest_session_minutes INTEGER DEFAULT 0,
            social_media_minutes INTEGER DEFAULT 0,
            gaming_minutes INTEGER DEFAULT 0,
            work_minutes INTEGER DEFAULT 0,
            entertainment_minutes INTEGER DEFAULT 0,
            other_minutes INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Health alerts/recommendations log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            alert_date TEXT NOT NULL,
            alert_type TEXT NOT NULL,             -- warning, critical, recommendation
            category TEXT NOT NULL,               -- mental_health, physical, usage
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ─── Mental Health Check-in Operations ───────────────────────────────────────

def save_checkin(data: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO mental_health_checkins
            (checkin_date, mood_score, anxiety_level, stress_level,
             sleep_hours, sleep_quality, energy_level, social_interaction, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("checkin_date", str(date.today())),
        data["mood_score"],
        data["anxiety_level"],
        data["stress_level"],
        data.get("sleep_hours"),
        data.get("sleep_quality"),
        data.get("energy_level"),
        data.get("social_interaction"),
        data.get("notes", ""),
    ))
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_checkin_today():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM mental_health_checkins WHERE checkin_date = ? ORDER BY id DESC LIMIT 1",
        (str(date.today()),)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_checkins_last_n_days(n: int = 7) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM mental_health_checkins
        ORDER BY checkin_date DESC
        LIMIT ?
    """, (n,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Phone Usage Operations ───────────────────────────────────────────────────

def log_usage_session(data: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO phone_usage_sessions
            (usage_date, app_category, duration_minutes, session_start, session_end)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data.get("usage_date", str(date.today())),
        data["app_category"],
        data["duration_minutes"],
        data.get("session_start"),
        data.get("session_end"),
    ))
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    _update_daily_summary(data.get("usage_date", str(date.today())))
    return row_id


def _update_daily_summary(usage_date: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            SUM(duration_minutes) as total,
            MAX(duration_minutes) as longest,
            SUM(CASE WHEN app_category='social_media' THEN duration_minutes ELSE 0 END) as social,
            SUM(CASE WHEN app_category='gaming' THEN duration_minutes ELSE 0 END) as gaming,
            SUM(CASE WHEN app_category='work' THEN duration_minutes ELSE 0 END) as work,
            SUM(CASE WHEN app_category='entertainment' THEN duration_minutes ELSE 0 END) as entertain,
            SUM(CASE WHEN app_category='other' THEN duration_minutes ELSE 0 END) as other,
            COUNT(*) as sessions
        FROM phone_usage_sessions
        WHERE usage_date = ?
    """, (usage_date,))
    row = cursor.fetchone()
    if row:
        cursor.execute("""
            INSERT INTO daily_usage_summary
                (summary_date, total_screen_time_minutes, pickups_count,
                 longest_session_minutes, social_media_minutes, gaming_minutes,
                 work_minutes, entertainment_minutes, other_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(summary_date) DO UPDATE SET
                total_screen_time_minutes = excluded.total_screen_time_minutes,
                pickups_count = excluded.pickups_count,
                longest_session_minutes = excluded.longest_session_minutes,
                social_media_minutes = excluded.social_media_minutes,
                gaming_minutes = excluded.gaming_minutes,
                work_minutes = excluded.work_minutes,
                entertainment_minutes = excluded.entertainment_minutes,
                other_minutes = excluded.other_minutes
        """, (
            usage_date,
            row["total"] or 0,
            row["sessions"] or 0,
            row["longest"] or 0,
            row["social"] or 0,
            row["gaming"] or 0,
            row["work"] or 0,
            row["entertain"] or 0,
            row["other"] or 0,
        ))
    conn.commit()
    conn.close()


def get_usage_summary_today() -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM daily_usage_summary WHERE summary_date = ?",
        (str(date.today()),)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {
        "total_screen_time_minutes": 0, "pickups_count": 0,
        "longest_session_minutes": 0, "social_media_minutes": 0,
        "gaming_minutes": 0, "work_minutes": 0,
        "entertainment_minutes": 0, "other_minutes": 0,
    }


def get_usage_last_n_days(n: int = 7) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM daily_usage_summary
        ORDER BY summary_date DESC LIMIT ?
    """, (n,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Medical Ailment Operations ───────────────────────────────────────────────

def log_ailment(data: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO medical_ailments
            (log_date, ailment_type, severity, duration_minutes, possible_trigger, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data.get("log_date", str(date.today())),
        data["ailment_type"],
        data["severity"],
        data.get("duration_minutes"),
        data.get("possible_trigger", ""),
        data.get("notes", ""),
    ))
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_ailments_last_n_days(n: int = 7) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM medical_ailments
        ORDER BY log_date DESC, id DESC
        LIMIT ?
    """, (n * 5,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Health Alerts ────────────────────────────────────────────────────────────

def save_alert(alert_type: str, category: str, message: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO health_alerts (alert_date, alert_type, category, message)
        VALUES (?, ?, ?, ?)
    """, (str(date.today()), alert_type, category, message))
    conn.commit()
    conn.close()


def get_unread_alerts() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM health_alerts WHERE is_read = 0
        ORDER BY created_at DESC LIMIT 20
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_alerts_read():
    conn = get_connection()
    conn.execute("UPDATE health_alerts SET is_read = 1 WHERE is_read = 0")
    conn.commit()
    conn.close()


# ─── User Profile ─────────────────────────────────────────────────────────────

def get_or_create_user(name: str = "User", age: int = 25, gender: str = "Prefer not to say") -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users LIMIT 1")
    row = cursor.fetchone()
    if not row:
        cursor.execute(
            "INSERT INTO users (name, age, gender) VALUES (?, ?, ?)",
            (name, age, gender)
        )
        conn.commit()
        cursor.execute("SELECT * FROM users LIMIT 1")
        row = cursor.fetchone()
    conn.close()
    return dict(row)


def update_user(name: str, age: int, gender: str):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET name=?, age=?, gender=? WHERE id=1",
        (name, age, gender)
    )
    conn.commit()
    conn.close()
