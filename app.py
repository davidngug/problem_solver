from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app
import jwt
import datetime

app = Flask(__name__)

# Secret key for JWT encoding/decoding
app.config['SECRET_KEY'] = '908a8a7d7524deb6b09185512f07cb3e58b8e63e471eaf543b0ad05cfdcc0277'

# Initialize Firebase Admin SDK
cred = credentials.Certificate("business-solver-firebase-adminsdk-fbsvc-5aa3b74d8f.json")
initialize_app(cred)
db = firestore.client()

users_ref = db.collection('users')

def token_required(f):
    """
    Decorator to protect routes with JWT authentication.
    """
    def decorator(*args, **kwargs):
        token = None

        # Check if the token is passed in the Authorization header
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]  # Get token after 'Bearer'

        if not token:
            return jsonify({'message': 'Token is missing!'}), 403

        try:
            # Decode the token to get the user info
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['email']  # Email is used as the identifier
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 403

        return f(current_user, *args, **kwargs)  # Pass current_user to the protected route

    return decorator

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
        # Generate JWT token
        token = jwt.encode({
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # 1 hour expiration
        }, app.config['SECRET_KEY'], algorithm="HS256")

        return jsonify({'message': 'Login successful!', 'token': token}), 200

    return jsonify({"error": "Invalid credentials!"}), 401

@app.route('/test', methods=['GET'])
@token_required
def test_connection(current_user):
    try:
        # Test Firestore connection and fetch all users
        docs = users_ref.stream()
        
        # Create a list to store user data
        user_list = []
        for doc in docs:
            user_data = doc.to_dict()
            user_list.append(user_data)

        return jsonify({
            "message": "Connection successful!",
            "users": user_list,  # Returning the list of users
            "current_user": current_user  # Show the email of the authenticated user
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Business Solver API!"}), 200

# Print all available routes
print(app.url_map)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


