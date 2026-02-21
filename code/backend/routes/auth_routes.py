"""
Authentication Routes for LIFEXIA
Simple token-based authentication for the web interface
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
import logging
import hashlib
import secrets

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# Simple in-memory user storage (use database in production)
users_db = {}
tokens_db = {}

# Default admin account
ADMIN_EMAIL = 'admin@lifexia.com'
ADMIN_PASSWORD = 'admin123'


def generate_token():
    """Generate a secure random token"""
    return secrets.token_hex(32)


def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with email and password"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password required'
            }), 400

        # Check admin account
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            token = generate_token()
            tokens_db[token] = {
                'email': email,
                'role': 'admin',
                'created_at': datetime.now().isoformat()
            }
            return jsonify({
                'success': True,
                'token': token,
                'user': {
                    'email': email,
                    'name': 'Admin',
                    'role': 'admin'
                }
            })

        # Check registered users
        if email in users_db:
            user = users_db[email]
            if user.get('password_hash') == hash_password(password):
                token = generate_token()
                tokens_db[token] = {
                    'email': email,
                    'role': 'user',
                    'created_at': datetime.now().isoformat()
                }
                return jsonify({
                    'success': True,
                    'token': token,
                    'user': {
                        'email': email,
                        'name': user.get('name', 'User'),
                        'role': 'user'
                    }
                })

        # Auto-register new users (for demo)
        token = generate_token()
        users_db[email] = {
            'email': email,
            'name': email.split('@')[0].title(),
            'password_hash': hash_password(password),
            'created_at': datetime.now().isoformat(),
            'role': 'user'
        }
        tokens_db[token] = {
            'email': email,
            'role': 'user',
            'created_at': datetime.now().isoformat()
        }

        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'email': email,
                'name': users_db[email]['name'],
                'role': 'user'
            },
            'message': 'Account created successfully'
        })

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'error': 'Login failed'
        }), 500


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user account"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name = data.get('name', '')

        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password required'
            }), 400

        if email in users_db:
            return jsonify({
                'success': False,
                'error': 'Email already registered'
            }), 409

        users_db[email] = {
            'email': email,
            'name': name or email.split('@')[0].title(),
            'password_hash': hash_password(password),
            'created_at': datetime.now().isoformat(),
            'role': 'user'
        }

        token = generate_token()
        tokens_db[token] = {
            'email': email,
            'role': 'user',
            'created_at': datetime.now().isoformat()
        }

        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'email': email,
                'name': users_db[email]['name'],
                'role': 'user'
            }
        })

    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'success': False, 'error': 'Registration failed'}), 500


@auth_bp.route('/verify', methods=['POST'])
def verify_token():
    """Verify if a token is still valid"""
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else ''

        if not token:
            token = request.json.get('token', '') if request.json else ''

        if token and token in tokens_db:
            token_data = tokens_db[token]
            return jsonify({
                'valid': True,
                'email': token_data['email'],
                'role': token_data.get('role', 'user')
            })

        return jsonify({'valid': False}), 401

    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return jsonify({'valid': False}), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user and invalidate token"""
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else ''

        if token and token in tokens_db:
            del tokens_db[token]

        session.clear()
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })

    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'success': True, 'message': 'Logged out'})


@auth_bp.route('/session', methods=['GET'])
def get_session():
    """Get current session info"""
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else ''

        if token and token in tokens_db:
            token_data = tokens_db[token]
            email = token_data['email']
            user = users_db.get(email, {'email': email, 'name': 'Admin', 'role': 'admin'})
            return jsonify({
                'success': True,
                'logged_in': True,
                'user': {
                    'email': email,
                    'name': user.get('name', 'User'),
                    'role': token_data.get('role', 'user')
                }
            })

        return jsonify({
            'success': True,
            'logged_in': False
        })

    except Exception as e:
        logger.error(f"Session check error: {e}")
        return jsonify({'success': True, 'logged_in': False})
