"""
database.py
===========
Handles all SQLite database operations for the Smart Attendance System.

This module:
- Creates the database and tables if they don't exist
- Stores attendance records (name, date, time)
- Prevents duplicate attendance for the same student on the same day
- Provides functions to query attendance records
"""

import sqlite3
from datetime import datetime
import os

# Path to the SQLite database file
DATABASE_PATH = "attendance.db"


def get_db_connection():
    """
    Create and return a connection to the SQLite database.
    Returns:
        sqlite3.Connection: Database connection object
    """
    conn = sqlite3.connect(DATABASE_PATH)
    # Return rows as dictionaries for easier access
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """
    Initialize the database by creating the attendance table if it doesn't exist.
    This function is called when the app starts.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create attendance table with:
    # - id: unique identifier for each record
    # - name: student's name
    # - date: date of attendance (YYYY-MM-DD format)
    # - time: time of attendance (HH:MM:SS format)
    # - created_at: timestamp when record was created
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("[INFO] Database initialized successfully.")


def mark_attendance(name):
    """
    Mark attendance for a student.
    Prevents duplicate entries for the same student on the same day.

    Args:
        name (str): Student's name

    Returns:
        dict: Result with success status and message
    """
    # Get current date and time
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if student already has attendance marked for today
    cursor.execute(
        "SELECT * FROM attendance WHERE name = ? AND date = ?",
        (name, current_date)
    )
    existing_record = cursor.fetchone()

    if existing_record:
        # Student already marked attendance today
        conn.close()
        return {
            "success": False,
            "message": f"Attendance already marked for {name} today at {existing_record['time']}"
        }

    # Insert new attendance record
    cursor.execute(
        "INSERT INTO attendance (name, date, time) VALUES (?, ?, ?)",
        (name, current_date, current_time)
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"Attendance marked for {name} at {current_time}",
        "name": name,
        "date": current_date,
        "time": current_time
    }


def get_all_attendance():
    """
    Retrieve all attendance records from the database.

    Returns:
        list: List of dictionaries containing attendance records
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM attendance ORDER BY date DESC, time DESC"
    )
    rows = cursor.fetchall()

    # Convert rows to list of dictionaries
    attendance_list = []
    for row in rows:
        attendance_list.append({
            "id": row["id"],
            "name": row["name"],
            "date": row["date"],
            "time": row["time"],
            "created_at": row["created_at"]
        })

    conn.close()
    return attendance_list


def get_attendance_by_date(date):
    """
    Retrieve attendance records for a specific date.

    Args:
        date (str): Date in YYYY-MM-DD format

    Returns:
        list: List of attendance records for the given date
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM attendance WHERE date = ? ORDER BY time DESC",
        (date,)
    )
    rows = cursor.fetchall()

    attendance_list = []
    for row in rows:
        attendance_list.append({
            "id": row["id"],
            "name": row["name"],
            "date": row["date"],
            "time": row["time"]
        })

    conn.close()
    return attendance_list


def get_student_attendance(name):
    """
    Retrieve all attendance records for a specific student.

    Args:
        name (str): Student's name

    Returns:
        list: List of attendance records for the student
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM attendance WHERE name = ? ORDER BY date DESC, time DESC",
        (name,)
    )
    rows = cursor.fetchall()

    attendance_list = []
    for row in rows:
        attendance_list.append({
            "id": row["id"],
            "name": row["name"],
            "date": row["date"],
            "time": row["time"]
        })

    conn.close()
    return attendance_list


def clear_attendance():
    """
    Clear all attendance records from the database.
    Use with caution - this deletes all records!

    Returns:
        dict: Result with success status and message
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM attendance")

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "All attendance records cleared"
    }

