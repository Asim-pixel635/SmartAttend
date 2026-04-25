"""
app.py
======
Main Flask application for the Smart Attendance System with Face Recognition.

This application provides:
- Student registration with face capture
- Automatic attendance marking using face recognition
- Attendance records management
- REST API endpoints for all operations
- Simple web UI for easy interaction

Run with: python app.py
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os

# Import our custom modules
import database
import face_utils

# Create Flask application
app = Flask(__name__)

# Enable CORS so the frontend can communicate with the backend
CORS(app)

# Initialize components when the app starts
print("=" * 60)
print("SmartAttend - Smart Attendance System")
print("=" * 60)

# Create database tables
print("[INFO] Initializing database...")
database.init_database()

# Load all registered student faces
print("[INFO] Loading registered student faces...")
face_utils.load_known_faces()

print("=" * 60)


# ============================
# Frontend Routes
# ============================

@app.route('/')
def home():
    """
    Home page - renders the main UI for the attendance system.
    """
    return render_template('index.html')


@app.route('/api/health')
def health_check():
    """
    Health check endpoint to verify the server is running.
    """
    return jsonify({
        "status": "running",
        "service": "SmartAttend",
        "registered_students": len(face_utils.known_face_names),
        "attendance_records": len(database.get_all_attendance())
    })


# ============================
# Student Registration API
# ============================

@app.route('/api/register/<name>', methods=['POST'])
def register_student(name):
    """
    Register a new student with face recognition.
    Opens the webcam, captures the student's face, and saves the encoding.

    Args:
        name (str): Student's name (from URL parameter)

    Returns:
        JSON: Registration result
    """
    if not name or not name.strip():
        return jsonify({
            "success": False,
            "message": "Student name is required"
        }), 400

    print(f"[INFO] Registering student: {name}")

    # Attempt to register the student
    result = face_utils.register_student(name)

    if result["success"]:
        # Return success with 201 Created status
        return jsonify(result), 201
    else:
        # Return error with 400 Bad Request status
        return jsonify(result), 400


@app.route('/api/register', methods=['POST'])
def register_student_body():
    """
    Alternative registration endpoint that accepts name in request body.
    Useful for POST requests with JSON payloads.
    """
    data = request.get_json(silent=True)

    if not data or 'name' not in data:
        return jsonify({
            "success": False,
            "message": "Missing 'name' field in request body"
        }), 400

    name = data['name'].strip()
    if not name:
        return jsonify({
            "success": False,
            "message": "Student name cannot be empty"
        }), 400

    print(f"[INFO] Registering student: {name}")
    result = face_utils.register_student(name)

    if result["success"]:
        return jsonify(result), 201
    else:
        return jsonify(result), 400


# ============================
# Attendance Marking API
# ============================

@app.route('/api/mark_attendance', methods=['POST'])
def mark_attendance():
    """
    Mark attendance using face recognition.
    Opens webcam, detects face, matches with registered students, and records attendance.
    Prevents duplicate attendance for the same student on the same day.

    Returns:
        JSON: Attendance result
    """
    # Check if there are any registered students
    if len(face_utils.known_face_encodings) == 0:
        return jsonify({
            "success": False,
            "message": "No students registered. Please register students first."
        }), 400

    print("[INFO] Starting attendance marking process...")

    # Perform face recognition
    recognition_result = face_utils.recognize_faces(duration=5)

    if not recognition_result["success"]:
        return jsonify(recognition_result), 400

    recognized_name = recognition_result["name"]
    print(f"[INFO] Face recognized: {recognized_name}")

    # Mark attendance in database
    attendance_result = database.mark_attendance(recognized_name)

    # Combine recognition and attendance results
    response = {
        "success": attendance_result["success"],
        "message": attendance_result["message"],
        "name": recognized_name,
        "confidence": recognition_result.get("confidence", 0)
    }

    if attendance_result["success"]:
        print(f"[INFO] Attendance marked for: {recognized_name}")
        return jsonify(response), 200
    else:
        print(f"[INFO] {attendance_result['message']}")
        return jsonify(response), 200  # Still return 200 for duplicate


# ============================
# Attendance Records API
# ============================

@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    """
    Retrieve all attendance records.

    Returns:
        JSON: List of all attendance records
    """
    records = database.get_all_attendance()
    return jsonify({
        "success": True,
        "count": len(records),
        "attendance": records
    })


@app.route('/api/attendance/today', methods=['GET'])
def get_today_attendance():
    """
    Retrieve today's attendance records.

    Returns:
        JSON: List of today's attendance records
    """
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    records = database.get_attendance_by_date(today)
    return jsonify({
        "success": True,
        "date": today,
        "count": len(records),
        "attendance": records
    })


@app.route('/api/attendance/student/<name>', methods=['GET'])
def get_student_attendance(name):
    """
    Retrieve attendance records for a specific student.

    Args:
        name (str): Student's name

    Returns:
        JSON: List of student's attendance records
    """
    if not name:
        return jsonify({
            "success": False,
            "message": "Student name is required"
        }), 400

    records = database.get_student_attendance(name)
    return jsonify({
        "success": True,
        "student": name,
        "count": len(records),
        "attendance": records
    })


# ============================
# Student Management API
# ============================

@app.route('/api/students', methods=['GET'])
def get_registered_students():
    """
    Get a list of all registered students.

    Returns:
        JSON: List of student names
    """
    students = face_utils.get_registered_students()
    return jsonify({
        "success": True,
        "count": len(students),
        "students": students
    })


@app.route('/api/students/reload', methods=['POST'])
def reload_students():
    """
    Reload all student faces from the students folder.
    Useful after manually adding images to the folder.

    Returns:
        JSON: Reload result
    """
    encodings, names = face_utils.load_known_faces()
    return jsonify({
        "success": True,
        "message": f"Reloaded {len(names)} students",
        "count": len(names),
        "students": names
    })


@app.route('/api/attendance/clear', methods=['POST'])
def clear_attendance():
    """
    Clear all attendance records from the database.
    Use with caution!

    Returns:
        JSON: Clear result
    """
    result = database.clear_attendance()
    return jsonify(result)


# ============================
# Main Entry Point
# ============================

if __name__ == '__main__':
    print("[INFO] Starting SmartAttend server...")
    print("[INFO] API endpoints:")
    print("  - GET  /                    -> Web UI")
    print("  - GET  /api/health          -> Health check")
    print("  - POST /api/register/<name> -> Register student")
    print("  - POST /api/mark_attendance -> Mark attendance")
    print("  - GET  /api/attendance      -> Get all records")
    print("  - GET  /api/students        -> Get registered students")
    print("[INFO] Press Ctrl+C to stop the server")
    print("=" * 60)

    # Run the Flask development server
    # host='0.0.0.0' makes it accessible from other devices on the network
    app.run(host='0.0.0.0', port=5000, debug=True)

