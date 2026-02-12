from flask import Blueprint, request, jsonify
import jwt
import datetime
from backend.config import Config

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    # Basic mock authentication for now
    if email and password:
        token = jwt.encode({
            'user': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, Config.SECRET_KEY, algorithm="HS256")
        
        return jsonify({'token': token}), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/verify', methods=['POST'])
def verify():
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            return jsonify({'valid': True}), 200
        except:
            pass
    return jsonify({'valid': False}), 401
