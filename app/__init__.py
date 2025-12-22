"""
Text Augmentation API Application Factory
"""
import os
from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.extensions import limiter, swagger

def create_app(config_class=Config):
    """
    Application factory pattern for Flask
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Initialize extensions
    CORS(app)
    
    # Rate limiting - initialize after app context
    limiter.init_app(app)
    
    # Swagger documentation
    swagger.init_app(app)
    
    # Register blueprints
    from app.api.v1.routes import bp as api_v1_bp
    from app.api.health import bp as health_bp
    from app.api.v1.batch_routes import bp as batch_bp
    from app.api.v1.sentiment_routes import bp as sentiment_bp
    from app.api.v1.public_routes import bp as public_bp  # Add this if you created public_routes.py
    from app.features.routes import bp as features_bp
    from app.frontend_routes import bp as frontend_bp

    
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    app.register_blueprint(health_bp, url_prefix='/health')
    app.register_blueprint(batch_bp, url_prefix='/api/v1')
    app.register_blueprint(sentiment_bp, url_prefix='/api/v1')
    app.register_blueprint(public_bp, url_prefix='/api/v1')  # Add this if you created public_routes.py
    # Register it in create_app function
    app.register_blueprint(features_bp, url_prefix='/api/v1')
    # Register it in create_app function
    app.register_blueprint(frontend_bp)
    # Import and register error handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Print startup message
    @app.before_first_request
    def startup_message():
        app.logger.info("Text Augmentation API started successfully!")
    
    return app