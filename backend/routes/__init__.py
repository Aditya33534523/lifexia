"""
Routes package for LIFEXIA
"""

from .chat_routes import chat_bp
from .whatsapp_routes import whatsapp_bp
from .webhook_routes import webhook_bp
from .map_routes import map_bp
from .auth_routes import auth_bp

__all__ = ['chat_bp', 'whatsapp_bp', 'webhook_bp', 'map_bp', 'auth_bp']