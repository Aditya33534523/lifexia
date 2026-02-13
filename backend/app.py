from flask import Flask, render_template, Response
from flask_cors import CORS
from backend.config import config
from backend.utils import init_db
from backend.services.whatsapp_service import WhatsAppService
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app(config_name='default'):
    print(f"Creating app with config: {config_name}")
    app = Flask(__name__, 
                template_folder='../frontend/templates',
                static_folder='../frontend/static')
    
    app.config.from_object(config[config_name])
    CORS(app)
    init_db(app)
    
    # Initialize WhatsApp Service
    whatsapp_service = WhatsAppService(
        access_token=app.config['WHATSAPP_ACCESS_TOKEN'],
        phone_number_id=app.config['WHATSAPP_PHONE_NUMBER_ID']
    )
    
    # Import blueprints
    from backend.routes.auth_routes import auth_bp
    from backend.routes.chat_routes import chat_bp, init_chat_whatsapp
    from backend.routes.whatsapp_routes import whatsapp_bp, init_whatsapp_service
    from backend.routes.history_routes import history_bp
    from backend.routes.upload_routes import upload_bp
    from backend.routes.webhook_routes import webhook_bp, init_webhook_service
    from backend.routes.map_routes import map_bp
    
    # Initialize services in routes
    init_whatsapp_service(whatsapp_service)
    init_webhook_service(whatsapp_service)
    init_chat_whatsapp(whatsapp_service)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(whatsapp_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(webhook_bp)
    app.register_blueprint(map_bp)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/favicon.ico')
    @app.route('/apple-touch-icon.png')
    @app.route('/apple-touch-icon-precomposed.png')
    def app_icon_placeholders():
        return Response(status=204)

    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'LifeXia'}, 200
    
    print("App creation complete")
    return app

print(f"App module loaded. Name: {__name__}")

if __name__ == '__main__':
    print("Starting app execution...")
    try:
        app = create_app()
        print("App instance created. Calling run()...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"CRITICAL ERROR starting app: {e}")
        import traceback
        traceback.print_exc()