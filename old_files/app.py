from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

attendance = []

@app.route('/')
def home():
    return "SmartAttend Server Running"

@app.route('/mark', methods=['POST'])
def mark():
    data = request.get_json(silent=True)
    if not data or 'name' not in data:
        return jsonify({"error": "Missing 'name' field"}), 400
    name = data['name'].strip()
    if not name:
        return jsonify({"error": "Name cannot be empty"}), 400
    attendance.append(name)
    return jsonify({"message": f"{name} added"})

@app.route('/attendance', methods=['GET'])
def get_attendance():
    return jsonify({"attendance": attendance})

if __name__ == '__main__':
    app.run(debug=True)

