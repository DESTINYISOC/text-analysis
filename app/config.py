"""
Configuration settings for the Text Augmentation API
"""
import os
from datetime import timedelta

class Config:
    """Base configuration."""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # API Settings
    API_TITLE = "Text Augmentation API"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = "An API for text enrichment with sentiment analysis and synonym augmentation"
    
    # Swagger
    SWAGGER = {
        'title': API_TITLE,
        'uiversion': 3,
        'specs_route': '/api/docs/',
        'static_url_path': '/static/swagger-ui/',
        'specs': [{
            'endpoint': 'apispec',
            'route': '/api/docs/apispec.json',
            'rule_filter': lambda rule: True,
            'model_filter': lambda tag: True,
        }],
    }
    
    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_STORAGE_URI = "memory://"
    
    # Text Processing Limits
    MAX_SENTENCE_LENGTH = 1000
    MAX_SYNONYM_COUNT = 10
    MIN_SENTENCE_LENGTH = 2
    
    # File Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    RATELIMIT_DEFAULT = "1000 per hour"  # More generous in dev

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    RATELIMIT_ENABLED = False
    SECRET_KEY = 'test-secret-key'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
    # Use environment variable for secret key in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Stricter rate limiting in production
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Use Redis for rate limiting in production
    RATELIMIT_STORAGE_URI = os.environ.get('REDIS_URL', 'memory://')
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to stdout for Docker/containerized environments
        import logging
        from logging import StreamHandler
        handler = StreamHandler()
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
