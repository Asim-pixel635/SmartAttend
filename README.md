# SmartAttend - AI-Powered Face Recognition Attendance System

A complete smart attendance system that uses **Face Recognition** to automatically mark attendance. Built with Python, Flask, OpenCV, and SQLite.

## Features

### Student Registration
- Capture face using webcam
- Save face image in `students/` folder
- Generate unique face encoding for recognition

### Face Recognition Attendance
- Real-time face detection using OpenCV
- Match detected faces with stored encodings
- Automatically mark attendance with confidence score

### Attendance Management
- Store name, date, and time in SQLite database
- Prevent duplicate attendance for same student on same day
- View all attendance records and today's records
- Clear attendance data when needed

### Web Interface
- Clean, responsive web UI
- Real-time stats (registered students, today's attendance)
- Student registration with one click
- Attendance marking with face recognition
- View and manage attendance records

## Project Structure

```
SmartAttend/
├── app.py                 # Main Flask application
├── database.py            # SQLite database operations
├── face_utils.py          # Face detection & recognition logic
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── students/              # Folder to store student images
└── templates/
    └── index.html         # Web UI
```

## Tech Stack

| Technology | Purpose |
|------------|---------|
| **Python** | Backend programming |
| **Flask** | Web framework & API |
| **OpenCV** | Computer vision & webcam access |
| **face-recognition** | Face detection & recognition |
| **SQLite** | Database for attendance records |
| **HTML/CSS/JS** | Frontend web interface |

## Prerequisites

Before installing, make sure you have:

1. **Python 3.8+** installed
2. **CMake** installed (required for dlib, which is a dependency of face-recognition)
   - Download from: https://cmake.org/download/
   - Make sure to add CMake to your system PATH during installation
3. **Webcam** connected to your computer

## Installation Steps

### Step 1: Install CMake (Important!)

**Windows:**
1. Go to https://cmake.org/download/
2. Download the Windows installer
3. Run the installer and make sure to check "Add CMake to the system PATH for all users"
4. Restart your computer after installation

### Step 2: Install Python Dependencies

Open a terminal/command prompt and navigate to the project folder:

```bash
cd SmartAttend
```

Install all required packages:

```bash
pip install -r requirements.txt
```

**Note:** The first time you install `face-recognition`, it may take several minutes because it needs to compile dlib.

### Step 3: Create the Students Folder

The `students/` folder is automatically created when you run the app, but you can create it manually:

```bash
mkdir students
```

## How to Run

### Step 1: Start the Server

In the terminal, run:

```bash
python app.py
```

You should see output like:
```
============================================================
SmartAttend - Smart Attendance System
============================================================
[INFO] Initializing database...
[INFO] Loading registered student faces...
[INFO] Loaded 0 student faces.
============================================================
[INFO] Starting SmartAttend server...
[INFO] API endpoints:
  - GET  /                    -> Web UI
  - GET  /api/health          -> Health check
  - POST /api/register        -> Register student
  - POST /api/mark_attendance -> Mark attendance
  - GET  /api/attendance      -> Get all records
  - GET  /api/students        -> Get registered students
[INFO] Press Ctrl+C to stop the server
============================================================
 * Running on http://127.0.0.1:5000
```

### Step 2: Open the Web Interface

Open your web browser and go to:

```
http://127.0.0.1:5000
```

### Step 3: Use the System

**Register a Student:**
1. Enter the student's name in the form
2. Click "Register Student"
3. Look at the webcam when it opens (wait 3 seconds for capture)
4. The face image is saved and encoding is generated

**Mark Attendance:**
1. Click "Mark Attendance"
2. Look at the webcam when it opens (runs for 5 seconds)
3. The system detects and matches your face
4. Attendance is automatically recorded

**View Records:**
- Click "Refresh Records" to see all attendance data
- Click "Today's Only" to see today's records

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Web UI |
| GET | `/api/health` | Server health check |
| POST | `/api/register` | Register student with face capture |
| POST | `/api/register/{name}` | Register student (URL param) |
| POST | `/api/mark_attendance` | Mark attendance via face recognition |
| GET | `/api/attendance` | Get all attendance records |
| GET | `/api/attendance/today` | Get today's attendance records |
| GET | `/api/attendance/student/{name}` | Get records for specific student |
| GET | `/api/students` | Get list of registered students |
| POST | `/api/students/reload` | Reload student faces from folder |
| POST | `/api/attendance/clear` | Clear all attendance records |

### Example API Usage

**Register a student:**
```bash
curl -X POST http://127.0.0.1:5000/api/register/JohnDoe
```

**Mark attendance:**
```bash
curl -X POST http://127.0.0.1:5000/api/mark_attendance
```

**Get attendance records:**
```bash
curl http://127.0.0.1:5000/api/attendance
```

## Adding Student Images Manually

You can add existing photos directly to the `students/` folder:

1. Place JPG/PNG images in the `students/` folder
2. Name the file exactly as the student's name (e.g., `John_Doe.jpg`)
3. Click "Reload List" or restart the server
4. The system will automatically generate face encodings for the new images

## Troubleshooting

### face-recognition installation fails

**Problem:** `pip install face-recognition` fails with dlib compilation errors.

**Solution:**
1. Install CMake first (see Step 1 above)
2. Restart your computer
3. Try installing again: `pip install dlib` then `pip install face-recognition`
4. On Windows, you may also need Visual C++ Build Tools

### Webcam not detected

**Problem:** "Could not access webcam" error.

**Solutions:**
1. Make sure your webcam is connected
2. Check if another application is using the webcam
3. On Windows, check Privacy Settings → Camera → Allow apps to access camera
4. Try using a different camera index in `face_utils.py` (change `cv2.VideoCapture(0)` to `cv2.VideoCapture(1)`)

### No face detected

**Problem:** "No face detected" during registration or attendance.

**Solutions:**
1. Make sure your face is clearly visible
2. Improve lighting conditions
3. Move closer to the camera
4. Remove glasses or hats that may obscure your face

### Server won't start

**Problem:** Port 5000 is already in use.

**Solution:** Change the port in `app.py`:
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

## Security Notes

- This is a **development/demo** application
- The Flask development server should not be used in production
- Face images are stored as plain files in the `students/` folder
- The database file (`attendance.db`) contains all attendance records
- For production, consider using a proper WSGI server (Gunicorn, uWSGI) and HTTPS

## Future Enhancements

- Add support for multiple faces per student (different angles/lighting)
- Implement confidence threshold settings
- Add admin authentication and role-based access
- Export attendance to CSV/Excel
- Add email notifications for absent students
- Support for multiple classes/courses
- Machine learning model training for better accuracy

## License

This project is open source. Feel free to use, modify, and distribute.

## Credits

Built with:
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [OpenCV](https://opencv.org/) - Computer vision
- [face-recognition](https://github.com/ageitgey/face_recognition) - Face recognition
- [dlib](http://dlib.net/) - Machine learning toolkit

---

**Happy Attendance Marking!**

