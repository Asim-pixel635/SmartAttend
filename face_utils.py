"""
face_utils.py
=============
Handles all face detection and recognition operations for the Smart Attendance System.

This module:
- Loads and processes student images from the students/ folder
- Generates unique face encodings for each student using OpenCV
- Performs real-time face detection using webcam
- Matches detected faces with known students using histogram comparison
- Provides functions to register new students

NOTE: Uses OpenCV's built-in face detection as a fallback when face_recognition library
      is not available (which requires dlib compilation).
"""

import os
import cv2
import numpy as np

# Try to import face_recognition, fall back to OpenCV-only if not available
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("[WARNING] face_recognition not available. Using OpenCV fallback for face detection.")

# Folder to store student images
STUDENTS_FOLDER = "students"

# Global variables to store known face data
known_face_encodings = []   # List of face descriptors
known_face_names = []       # List of corresponding student names
known_face_images = []      # List of original images for histogram comparison

# Load OpenCV face detector
try:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    FACE_CASCADE_AVAILABLE = True
except:
    FACE_CASCADE_AVAILABLE = False
    face_cascade = None


def ensure_students_folder():
    """
    Create the students folder if it doesn't exist.
    This folder stores all registered student face images.
    """
    if not os.path.exists(STUDENTS_FOLDER):
        os.makedirs(STUDENTS_FOLDER)
        print(f"[INFO] Created '{STUDENTS_FOLDER}' folder.")


def detect_face_opencv(image):
    """
    Detect face using OpenCV Haar Cascade classifier.
    
    Args:
        image: numpy array (BGR image)
    
    Returns:
        tuple: (x, y, w, h) of face, or None
    """
    if not FACE_CASCADE_AVAILABLE:
        return None
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    if len(faces) > 0:
        # Return the largest face
        return max(faces, key=lambda f: f[2] * f[3])
    return None


def get_face_descriptor(image):
    """
    Get a face descriptor using available methods.
    
    Args:
        image: numpy array (BGR or RGB image)
    
    Returns:
        tuple: (descriptor, face_location) or (None, None)
    """
    if FACE_RECOGNITION_AVAILABLE:
        if len(image.shape) == 3 and image.shape[2] == 3:
            # Convert BGR to RGB if needed (assume BGR if from OpenCV)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb = image
        
        face_locations = face_recognition.face_locations(rgb)
        if len(face_locations) > 0:
            encodings = face_recognition.face_encodings(rgb, face_locations[:1])
            if encodings:
                return encodings[0], face_locations[0]
    else:
        # Use OpenCV fallback: compute color histogram of face region
        face = detect_face_opencv(image)
        if face is not None:
            x, y, w, h = face
            face_img = image[y:y+h, x:x+w]
            # Create descriptor from color histogram
            hist = cv2.calcHist([face_img], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            cv2.normalize(hist, hist)
            return hist.flatten(), face
    
    return None, None


def compare_faces(descriptor1, descriptor2):
    """
    Compare two face descriptors.
    
    Returns:
        float: similarity score (0-1, higher means more similar)
    """
    if FACE_RECOGNITION_AVAILABLE:
        # Use Euclidean distance for face_recognition encodings
        distance = np.linalg.norm(np.array(descriptor1) - np.array(descriptor2))
        return max(0, 1 - distance)
    else:
        # Use correlation for histograms
        correlation = cv2.compareHist(
            descriptor1.astype(np.float32),
            descriptor2.astype(np.float32),
            cv2.HISTCMP_CORREL
        )
        return max(0, correlation)


def load_known_faces():
    """
    Load all student images from the students/ folder and generate face descriptors.
    This function is called when the app starts and after new registrations.

    Returns:
        tuple: (list of face descriptors, list of student names)
    """
    global known_face_encodings, known_face_names, known_face_images

    # Reset the lists
    known_face_encodings = []
    known_face_names = []
    known_face_images = []

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
            # Load image file with OpenCV
            image = cv2.imread(image_path)
            if image is None:
                print(f"[WARNING] Could not load image: {image_file}")
                continue

            descriptor, face_loc = get_face_descriptor(image)

            if descriptor is not None:
                known_face_encodings.append(descriptor)
                known_face_names.append(name)
                known_face_images.append(image)
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

        # Detect face in the frame
        descriptor, face_loc = get_face_descriptor(frame)

        if descriptor is None:
            return {
                "success": False,
                "message": "No face detected. Please try again with better lighting."
            }

        # For face_recognition, check multiple faces
        if FACE_RECOGNITION_AVAILABLE and isinstance(face_loc, tuple):
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb)
            if len(face_locations) > 1:
                return {
                    "success": False,
                    "message": "Multiple faces detected. Please ensure only your face is visible."
                }

        # Save the captured image
        cv2.imwrite(image_path, frame)

        # Add to known faces
        known_face_encodings.append(descriptor)
        known_face_names.append(safe_name)
        known_face_images.append(frame)

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

            # Detect faces in the frame
            if FACE_RECOGNITION_AVAILABLE:
                # Resize frame for faster processing
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                for face_encoding, face_location in zip(face_encodings, face_locations):
                    # Compare face with known faces
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
                    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

                    name = "Unknown"
                    confidence = 0

                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = known_face_names[best_match_index]
                            confidence = 1 - face_distances[best_match_index]

                    # Scale face locations back to original size
                    top, right, bottom, left = face_location
                    top *= 4; right *= 4; bottom *= 4; left *= 4

                    # Draw rectangle around face
                    color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                    cv2.putText(frame, f"{name} ({confidence:.2f})",
                               (left + 6, bottom - 6),
                               cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

                    if name != "Unknown" and confidence > 0.5:
                        recognized_name = name
                        recognized_confidence = confidence
            else:
                # OpenCV fallback
                face = detect_face_opencv(frame)
                if face is not None:
                    x, y, w, h = face
                    # Draw rectangle
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                    # Get descriptor for current face
                    descriptor, _ = get_face_descriptor(frame)
                    if descriptor is not None:
                        best_match = -1
                        best_score = -1

                        for i, known_desc in enumerate(known_face_encodings):
                            score = compare_faces(known_desc, descriptor)
                            if score > best_score:
                                best_score = score
                                best_match = i

                        name = "Unknown"
                        confidence = 0
                        if best_match >= 0 and best_score > 0.3:
                            name = known_face_names[best_match]
                            confidence = best_score

                        cv2.putText(frame, f"{name} ({confidence:.2f})",
                                   (x, y - 10),
                                   cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

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

