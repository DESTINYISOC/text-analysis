"""
Swagger/OpenAPI utilities
"""
import yaml
from flask import current_app

def load_swagger_config():
    """Load Swagger configuration from YAML file if exists"""
    try:
        with open('swagger.yaml', 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        # Return default configuration
        return {
            'openapi': '3.0.0',
            'info': {
                'title': 'Text Augmentation API',
                'description': 'API for text enrichment with sentiment analysis and synonym augmentation',
                'version': '1.0.0'
            },
            'servers': [
                {
                    'url': 'http://localhost:5000',
                    'description': 'Development server'
                }
            ]
        }