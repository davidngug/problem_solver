from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app
from dotenv import load_dotenv  # Import dotenv to load environment variables
import os  # Import os to access environment variables
import jwt  # Import JWT for token generation and decoding
import datetime  # Import datetime for token expiration
import bcrypt  # Import bcrypt for secure password hashing

# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)

# Configure the secret key from the .env file
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

# Initialize Firebase Admin SDK
cred = credentials.Certificate("business-solver-firebase-adminsdk-fbsvc-5aa3b74d8f.json")
initialize_app(cred)
db = firestore.client()

users_ref = db.collection('users')


# Decorator to require JWT authentication
def token_required(f):
    def decorator(*args, **kwargs):
        token = None

        # Check if token is in the Authorization header
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]  # Get the token after "Bearer"

        if not token:
            return jsonify({'message': 'Token is missing!'}), 403

        try:
            # Decode the token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['email']  # Extract the user's email from the token
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 403

        return f(current_user, *args, **kwargs)  # Pass the user's email to the route

    return decorator


# Register a new user (with password hashing)
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required!"}), 400

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Add user to Firestore
    users_ref.document(email).set({
        "email": email,
        "password": hashed_password.decode('utf-8')  # Store as string
    })
    return jsonify({"message": "User registered successfully!"}), 201


# Login a user and return a JWT token (with hashed password check)
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required!"}), 400

    # Check user credentials
    user = users_ref.document(email).get()
    if user.exists:
        user_data = user.to_dict()
        stored_password = user_data.get('password')

        # Verify hashed password
        if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            # Generate JWT token
            token = jwt.encode({
                'email': email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # 1-hour expiration
            }, app.config['SECRET_KEY'], algorithm="HS256")

            return jsonify({'message': 'Login successful!', 'token': token}), 200

    return jsonify({"error": "Invalid credentials!"}), 401


# Test Firestore connection (secured)
@app.route('/test', methods=['GET'])
@token_required
def test_connection(current_user):
    try:
        # Test Firestore connection and fetch all users
        docs = users_ref.stream()
        user_list = []

        for doc in docs:
            user_list.append(doc.to_dict())

        return jsonify({
            "message": "Connection successful!",
            "users": user_list,
            "current_user": current_user
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Home route
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Business Solver API!"}), 200


# Print all available routes
print(app.url_map)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
