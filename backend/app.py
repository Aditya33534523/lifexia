"""
LIFEXIA - AI-Powered Pharma Healthcare Chatbot
Main Flask Application with RAG, WhatsApp, and Map Integration

FIXES APPLIED:
- Registered history_bp and upload_bp blueprints
- Fixed import paths
- Added proper error handling for all service initializations
"""

from flask import Flask, render_template, jsonify, request, session
from flask_cors import CORS
from flask_session import Session
import os
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """Application factory pattern"""
    app = Flask(__name__,
                template_folder='../frontend/templates',
                static_folder='../frontend/static')

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'lifexia-secret-key-2024')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['UPLOAD_FOLDER'] = 'data/uploads'

    # Enable CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Initialize session
    Session(app)

    # Import services
    from backend.services.rag_service import RAGService
    from backend.services.whatsapp_service import WhatsAppService
    from backend.services.map_service import MapService

    # Import routes
    from backend.routes.chat_routes import chat_bp
    from backend.routes.whatsapp_routes import whatsapp_bp
    from backend.routes.webhook_routes import webhook_bp, init_webhook_service
    from backend.routes.map_routes import map_bp
    from backend.routes.auth_routes import auth_bp
    from backend.routes.history_routes import history_bp
    from backend.routes.upload_routes import upload_bp

    # Initialize services
    rag_service = None
    whatsapp_service = None
    map_service = None

    try:
        rag_service = RAGService()
        logger.info("✅ RAG Service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG Service: {e}")

    try:
        whatsapp_access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        whatsapp_phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')

        if whatsapp_access_token and whatsapp_phone_id:
            whatsapp_service = WhatsAppService(whatsapp_access_token, whatsapp_phone_id)
            init_webhook_service(whatsapp_service)
            logger.info("✅ WhatsApp Service initialized successfully")
        else:
            logger.warning("⚠️ WhatsApp credentials not found in environment")
    except Exception as e:
        logger.error(f"❌ Failed to initialize WhatsApp Service: {e}")

    try:
        map_service = MapService()
        logger.info("✅ Map Service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Map Service: {e}")

    # Register blueprints
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(whatsapp_bp, url_prefix='/api/whatsapp')
    app.register_blueprint(webhook_bp, url_prefix='/api/whatsapp')
    app.register_blueprint(map_bp, url_prefix='/api/map')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(history_bp)  # already has url_prefix='/api/history'
    app.register_blueprint(upload_bp)   # already has url_prefix='/api/upload'

    # Make services available to routes
    app.config['RAG_SERVICE'] = rag_service
    app.config['WHATSAPP_SERVICE'] = whatsapp_service
    app.config['MAP_SERVICE'] = map_service

    # Main routes
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/chat')
    def chat_page():
        return render_template('chat.html')

    @app.route('/map')
    def map_page():
        return render_template('map.html')

    @app.route('/health')
    def health_check():
        services_status = {
            'rag_service': rag_service is not None,
            'whatsapp_service': whatsapp_service is not None,
            'map_service': map_service is not None
        }
        return jsonify({
            'status': 'healthy',
            'services': services_status,
            'timestamp': datetime.now().isoformat()
        })

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500

    return app


# Support both `python -m backend.app` and direct run
app = create_app()

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    os.makedirs('data/uploads', exist_ok=True)
    os.makedirs('flask_session', exist_ok=True)

    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'

    rag_active = app.config.get('RAG_SERVICE') is not None
    wa_active = app.config.get('WHATSAPP_SERVICE') is not None
    map_active = app.config.get('MAP_SERVICE') is not None

    logger.info(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║              🏥 LIFEXIA Healthcare Chatbot               ║
    ║                                                          ║
    ║  AI-Powered Drug Information & Emergency Assistance      ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    
    📡 Server running on: http://localhost:{port}
    🤖 RAG Service: {'✅ Active' if rag_active else '❌ Inactive (using built-in drug DB)'}
    📱 WhatsApp API: {'✅ Active' if wa_active else '❌ Inactive'}
    🗺️  Map Service: {'✅ Active' if map_active else '❌ Inactive'}
    
    📌 Routes:
       /              → Main chat interface (index.html)
       /chat          → Alternative chat (chat.html)
       /api/chat/*    → Chat API endpoints
       /api/whatsapp/* → WhatsApp API endpoints  
       /api/map/*     → Map API endpoints
       /api/auth/*    → Authentication endpoints
       /api/history/* → Chat history endpoints
       /health        → Health check
    """)

    app.run(host='0.0.0.0', port=port, debug=debug)
