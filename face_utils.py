"""
face_utils.py
=============
Handles all face detection and recognition operations for the Smart Attendance System.

This module:
- Loads and processes student images from the students/ folder
- Generates unique face encodings for each student
- Performs real-time face detection using webcam
- Matches detected faces with known students
- Provides functions to register new students
"""

import os
import cv2
import face_recognition
import numpy as np

# Folder to store student images
STUDENTS_FOLDER = "students"

# Global variables to store known face data
known_face_encodings = []   # List of face encoding arrays
known_face_names = []       # List of corresponding student names


def ensure_students_folder():
    """
    Create the students folder if it doesn't exist.
    This folder stores all registered student face images.
    """
    if not os.path.exists(STUDENTS_FOLDER):
        os.makedirs(STUDENTS_FOLDER)
        print(f"[INFO] Created '{STUDENTS_FOLDER}' folder.")


def load_known_faces():
    """
    Load all student images from the students/ folder and generate face encodings.
    This function is called when the app starts and after new registrations.

    Returns:
        tuple: (list of face encodings, list of student names)
    """
    global known_face_encodings, known_face_names

    # Reset the lists
    known_face_encodings = []
    known_face_names = []

    ensure_students_folder()

    # Get all image files in the students folder
    image_files = [f for f in os.listdir(STUDENTS_FOLDER)
                   if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    print(f"[INFO] Loading {len(image_files)} student images...")

    for image_file in image_files:
        # Extract student name from filename (remove extension)
        name = os.path.splitext(image_file)[0]
        image_path = os.path.join(STUDENTS_FOLDER, image_file)

        try:
            # Load image file
            image = face_recognition.load_image_file(image_path)

            # Get face encoding from the image
            # face_encodings returns a list; we take the first face found
            encodings = face_recognition.face_encodings(image)

            if len(encodings) > 0:
                known_face_encodings.append(encodings[0])
                known_face_names.append(name)
                print(f"[INFO] Loaded face for: {name}")
            else:
                print(f"[WARNING] No face found in image: {image_file}")

        except Exception as e:
            print(f"[ERROR] Failed to load {image_file}: {e}")

    print(f"[INFO] Loaded {len(known_face_names)} student faces.")
    return known_face_encodings, known_face_names


def register_student(name, frame=None):
    """
    Register a new student by capturing their face from the webcam.

    Args:
        name (str): Student's name
        frame (numpy.ndarray, optional): Pre-captured frame. If None, opens webcam.

    Returns:
        dict: Result with success status and message
    """
    ensure_students_folder()

    # Clean the name for use in filename (remove special characters)
    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_')

    if not safe_name:
        return {
            "success": False,
            "message": "Invalid name provided"
        }

    image_path = os.path.join(STUDENTS_FOLDER, f"{safe_name}.jpg")

    # Check if student already exists
    if os.path.exists(image_path):
        return {
            "success": False,
            "message": f"Student '{name}' is already registered"
        }

    try:
        if frame is None:
            # Open webcam and capture a frame
            cap = cv2.VideoCapture(0)

            if not cap.isOpened():
                return {
                    "success": False,
                    "message": "Could not access webcam"
                }

            print(f"[INFO] Look at the camera to register '{name}'...")
            print("[INFO] Capturing in 3 seconds...")

            # Wait a moment for camera to warm up
            import time
            time.sleep(3)

            ret, frame = cap.read()
            cap.release()

            if not ret:
                return {
                    "success": False,
                    "message": "Failed to capture image from webcam"
                }

        # Convert BGR (OpenCV format) to RGB (face_recognition format)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect face locations in the frame
        face_locations = face_recognition.face_locations(rgb_frame)

        if len(face_locations) == 0:
            return {
                "success": False,
                "message": "No face detected. Please try again with better lighting."
            }

        if len(face_locations) > 1:
            return {
                "success": False,
                "message": "Multiple faces detected. Please ensure only your face is visible."
            }

        # Get face encoding
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if len(face_encodings) == 0:
            return {
                "success": False,
                "message": "Could not generate face encoding. Please try again."
            }

        # Save the captured image
        cv2.imwrite(image_path, frame)

        # Add to known faces
        known_face_encodings.append(face_encodings[0])
        known_face_names.append(safe_name)

        print(f"[INFO] Student '{name}' registered successfully.")

        return {
            "success": True,
            "message": f"Student '{name}' registered successfully",
            "name": safe_name
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Registration failed: {str(e)}"
        }


def recognize_faces(duration=5):
    """
    Perform real-time face recognition using the webcam.
    Opens the webcam, detects faces, and matches them with known students.

    Args:
        duration (int): Number of seconds to run recognition

    Returns:
        dict: Result with recognized student name or error message
    """
    if len(known_face_encodings) == 0:
        return {
            "success": False,
            "message": "No registered students found. Please register students first."
        }

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return {
            "success": False,
            "message": "Could not access webcam"
        }

    recognized_name = None
    recognized_confidence = 0
    frame_count = 0

    print("[INFO] Starting face recognition... Look at the camera.")

    import time
    start_time = time.time()

    try:
        while (time.time() - start_time) < duration:
            ret, frame = cap.read()
            if not ret:
                continue

            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

            # Convert BGR to RGB
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Find all faces in the current frame
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for face_encoding, face_location in zip(face_encodings, face_locations):
                # Compare face with known faces
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

                name = "Unknown"
                confidence = 0

                if len(face_distances) > 0:
                    # Get the best match
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_face_names[best_match_index]
                        confidence = 1 - face_distances[best_match_index]

                # Scale face locations back to original size
                top, right, bottom, left = face_location
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw rectangle around face
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

                # Draw name label
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, f"{name} ({confidence:.2f})",
                           (left + 6, bottom - 6),
                           cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

                # If we found a known face with good confidence, record it
                if name != "Unknown" and confidence > 0.5:
                    recognized_name = name
                    recognized_confidence = confidence

            # Display the frame
            cv2.imshow('Smart Attendance - Face Recognition', frame)

            # Break if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            frame_count += 1

    finally:
        cap.release()
        cv2.destroyAllWindows()

    if recognized_name:
        # Replace underscores with spaces for display
        display_name = recognized_name.replace('_', ' ')
        return {
            "success": True,
            "name": display_name,
            "confidence": round(recognized_confidence, 2),
            "message": f"Recognized: {display_name} (confidence: {recognized_confidence:.2f})"
        }
    else:
        return {
            "success": False,
            "message": "No known face detected. Please try again."
        }


def get_registered_students():
    """
    Get a list of all registered students.

    Returns:
        list: List of student names
    """
    ensure_students_folder()
    image_files = [f for f in os.listdir(STUDENTS_FOLDER)
                   if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    students = []
    for image_file in image_files:
        name = os.path.splitext(image_file)[0].replace('_', ' ')
        students.append(name)

    return students

