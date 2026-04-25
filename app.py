from flask import Flask, request, jsonify
from flask_cors import CORS

# Create the Flask application
app = Flask(__name__)

# Enable CORS so the frontend can talk to the backend
CORS(app)

# In-memory storage for attendance records
attendance = []


@app.route('/')
def home():
    """
    Root endpoint.
    Returns a simple message to confirm the server is running.
    """
    return "SmartAttend Server Running"


@app.route('/mark', methods=['POST'])
def mark():
    """
    POST /mark
    Accepts JSON: {"name": "John Doe"}
    Stores the name in the attendance list.
    """
    data = request.get_json(silent=True)

    # Validate request has JSON and contains a 'name' key
    if not data or 'name' not in data:
        return jsonify({"error": "Missing 'name' field"}), 400

    # Clean up the name (remove extra spaces)
    name = data['name'].strip()

    # Reject empty names
    if not name:
        return jsonify({"error": "Name cannot be empty"}), 400

    # Save attendance
    attendance.append(name)

    return jsonify({"message": f"{name} added successfully"})


@app.route('/list', methods=['GET'])
def list_attendance():
    """
    GET /list
    Returns all stored attendance records.
    """
    return jsonify({"attendance": attendance})


# Run the server when this file is executed directly
if __name__ == '__main__':
    app.run(debug=True)

