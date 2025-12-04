# db_init.py
import sqlite3
from pathlib import Path

DB_PATH = Path("qwert.db")

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Faculty (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    department TEXT,
    phone TEXT
);

CREATE TABLE IF NOT EXISTS Subject (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT UNIQUE,
    credits INTEGER DEFAULT 3
);

CREATE TABLE IF NOT EXISTS ClassSchedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    faculty_id INTEGER NOT NULL,
    day_of_week TEXT NOT NULL,      -- e.g., Monday
    start_time TEXT NOT NULL,       -- e.g., 09:00
    end_time TEXT NOT NULL,         -- e.g., 10:00
    room TEXT,
    semester TEXT,
    FOREIGN KEY(subject_id) REFERENCES Subject(id) ON DELETE CASCADE,
    FOREIGN KEY(faculty_id) REFERENCES Faculty(id) ON DELETE SET NULL
);
"""

SAMPLE = [
    ("INSERT INTO Faculty (name, email, department, phone) VALUES (?, ?, ?, ?);",
     ("Dr. A. Kumar", "akumar@example.com", "CSE", "9000000001")),
    ("INSERT INTO Faculty (name, email, department, phone) VALUES (?, ?, ?, ?);",
     ("Ms. S. Rao", "srao@example.com", "ECE", "9000000002")),
    ("INSERT INTO Subject (name, code, credits) VALUES (?, ?, ?);",
     ("Data Structures", "CS201", 4)),
    ("INSERT INTO Subject (name, code, credits) VALUES (?, ?, ?);",
     ("Signals & Systems", "EC203", 4)),
]

def init_db(seed=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for stmt in SCHEMA.strip().split(";"):
        if stmt.strip():
            cur.execute(stmt)
    if seed:
        for sql, params in SAMPLE:
            try:
                cur.execute(sql, params)
            except Exception:
                pass
    conn.commit()
    conn.close()
    print(f"DB initialized at {DB_PATH.resolve()}")

if __name__ == "__main__":
    init_db(seed=True)
