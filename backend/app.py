from flask import Flask, render_template, Response
from flask_cors import CORS
from backend.config import config
from backend.utils import init_db

def create_app(config_name='default'):
    app = Flask(__name__, 
                template_folder='../frontend/templates',
                static_folder='../frontend/static')
    
    app.config.from_object(config[config_name])
    CORS(app)
    init_db(app)
    
    from backend.routes.webhook_routes import webhook_bp
    from backend.routes.map_routes import map_bp
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
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)