# models.py
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path("qwert.db")

def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

### Faculty CRUD ###
def get_all_faculty() -> List[Dict[str,Any]]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Faculty ORDER BY id;")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_faculty(faculty_id: int) -> Optional[Dict[str,Any]]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Faculty WHERE id=?;", (faculty_id,))
    r = cur.fetchone()
    conn.close()
    return dict(r) if r else None

def add_faculty(name: str, email: str="", department: str="", phone: str="") -> int:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO Faculty (name,email,department,phone) VALUES (?,?,?,?);",
                (name,email,department,phone))
    conn.commit()
    fid = cur.lastrowid
    conn.close()
    return fid

def update_faculty(faculty_id:int, name:str, email:str, department:str, phone:str) -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        UPDATE Faculty SET name=?, email=?, department=?, phone=? WHERE id=?;
    """, (name,email,department,phone,faculty_id))
    conn.commit()
    conn.close()

def delete_faculty(faculty_id:int) -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM Faculty WHERE id=?;", (faculty_id,))
    conn.commit()
    conn.close()

### Subject CRUD ###
def get_all_subjects() -> List[Dict[str,Any]]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Subject ORDER BY id;")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_subject(subject_id:int) -> Optional[Dict[str,Any]]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Subject WHERE id=?;", (subject_id,))
    r = cur.fetchone()
    conn.close()
    return dict(r) if r else None

def add_subject(name:str, code:str="", credits:int=3) -> int:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO Subject (name,code,credits) VALUES (?,?,?);",
                (name,code,credits))
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return sid

def update_subject(subject_id:int, name:str, code:str, credits:int) -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("UPDATE Subject SET name=?, code=?, credits=? WHERE id=?;",
                (name, code, credits, subject_id))
    conn.commit()
    conn.close()

def delete_subject(subject_id:int) -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM Subject WHERE id=?;", (subject_id,))
    conn.commit()
    conn.close()

### Schedule CRUD ###
def get_all_schedules() -> List[Dict[str,Any]]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT cs.*, s.name as subject_name, f.name as faculty_name
        FROM ClassSchedule cs
        LEFT JOIN Subject s ON cs.subject_id = s.id
        LEFT JOIN Faculty f ON cs.faculty_id = f.id
        ORDER BY cs.day_of_week, cs.start_time;
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_schedule(schedule_id:int) -> Optional[Dict[str,Any]]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ClassSchedule WHERE id=?;", (schedule_id,))
    r = cur.fetchone()
    conn.close()
    return dict(r) if r else None

def add_schedule(subject_id:int, faculty_id:int, day_of_week:str, start_time:str, end_time:str, room:str="", semester:str="") -> int:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ClassSchedule (subject_id,faculty_id,day_of_week,start_time,end_time,room,semester)
        VALUES (?,?,?,?,?,?,?);
    """, (subject_id,faculty_id,day_of_week,start_time,end_time,room,semester))
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return sid

def update_schedule(schedule_id:int, subject_id:int, faculty_id:int, day_of_week:str, start_time:str, end_time:str, room:str, semester:str) -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        UPDATE ClassSchedule
        SET subject_id=?, faculty_id=?, day_of_week=?, start_time=?, end_time=?, room=?, semester=?
        WHERE id=?;
    """, (subject_id,faculty_id,day_of_week,start_time,end_time,room,semester,schedule_id))
    conn.commit()
    conn.close()

def delete_schedule(schedule_id:int) -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM ClassSchedule WHERE id=?;", (schedule_id,))
    conn.commit()
    conn.close()
