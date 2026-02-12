#!/usr/bin/env python3
import os

# All backend files content
files = {
    "backend/models/__init__.py": """from .user import User
from .conversation import Conversation
from .message import Message
from .pharmacy_document import PharmacyDocument

__all__ = ['User', 'Conversation', 'Message', 'PharmacyDocument']
""",

    "backend/models/user.py": """from datetime import datetime
from backend.utils.database import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
""",

    "backend/models/conversation.py": """from datetime import datetime
from backend.utils.database import db

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    title = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'title': self.title,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'message_count': len(self.messages)
        }
""",

    "backend/models/message.py": """from datetime import datetime
from backend.utils.database import db

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    image_path = db.Column(db.String(500))
    metadata = db.Column(db.JSON)
    
    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'image_path': self.image_path
        }
""",

    "backend/models/pharmacy_document.py": """from datetime import datetime
from backend.utils.database import db

class PharmacyDocument(db.Model):
    __tablename__ = 'pharmacy_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), index=True)
    source = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'source': self.source
        }
""",

    "backend/utils/__init__.py": """from .database import db, init_db
from .validators import validate_email, validate_password, sanitize_input
from .helpers import get_timestamp, format_date, generate_session_id

__all__ = [
    'db', 'init_db',
    'validate_email', 'validate_password', 'sanitize_input',
    'get_timestamp', 'format_date', 'generate_session_id'
]
""",

    "backend/utils/database.py": """from flask_sqlalchemy import SQLAlchemy
import logging

logger = logging.getLogger(__name__)
db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        logger.info("Database initialized successfully")
""",

    "backend/utils/validators.py": """import re
from bleach import clean

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    return True, "Password is valid"

def sanitize_input(text):
    return clean(text, strip=True)
""",

    "backend/utils/helpers.py": """from datetime import datetime
import uuid

def get_timestamp():
    return datetime.utcnow()

def format_date(date, format_str='%Y-%m-%d %H:%M:%S'):
    if isinstance(date, datetime):
        return date.strftime(format_str)
    return date

def generate_session_id():
    return f"session_{uuid.uuid4().hex}"
"""
}

# Write all files
for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Created: {filepath}")

print("\\nAll backend model and utility files created successfully!")
