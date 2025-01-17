from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app

app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("business-solver-firebase-adminsdk-fbsvc-5aa3b74d8f.json")
initialize_app(cred)
db = firestore.client()

users_ref = db.collection('users')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    # Add user to Firestore
    users_ref.document(email).set({
        "email": email,
        "password": password  # Use a hashing library in production
    })
    return jsonify({"message": "User registered successfully!"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Check user credentials
    user = users_ref.document(email).get()
    if user.exists and user.to_dict().get('password') == password:
        return jsonify({"message": "Login successful!"}), 200
    return jsonify({"error": "Invalid credentials!"}), 401

@app.route('/test', methods=['GET'])
def test_connection():
    try:
        # Test Firestore connection
        docs = users_ref.stream()
        return jsonify({"message": "Connection successful!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Business Solver API!"}), 200

# Print all available routes
print(app.url_map)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


