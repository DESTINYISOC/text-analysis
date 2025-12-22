"""
Authentication middleware for validating requests
"""
from flask import request, jsonify, g
import re
from functools import wraps

from app.auth.models import user_manager
from app.utils.response import APIResponse

def require_auth(feature: str = None):
    """
    Decorator to require authentication and check tier limits
    
    Args:
        feature: Feature being accessed (for tier validation)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get API key from header or query parameter
            api_key = request.headers.get('X-API-Key') or \
                     request.headers.get('Authorization') or \
                     request.args.get('api_key')
            
            # Extract Bearer token if present
            if api_key and api_key.startswith('Bearer '):
                api_key = api_key[7:]
            
            # Get request parameters for validation
            request_data = request.get_json() or {}
            
            # Validate based on feature
            validation_kwargs = {}
            
            if feature == 'enrich_text':
                augmentation_count = request_data.get('augmentation_count', 3)
                text_length = len(request_data.get('text', ''))
                validation_kwargs = {
                    'augmentation_count': augmentation_count,
                    'text_length': text_length
                }
            
            elif feature == 'batch':
                batch_size = len(request_data.get('texts', []))
                validation_kwargs = {'batch_size': batch_size}
            
            elif feature == 'premium_feature':
                validation_kwargs = {}  # Just check if premium feature is allowed
            
            # Validate the request
            validation = user_manager.validate_request(
                api_key=api_key,
                feature=feature,
                **validation_kwargs
            )
            
            # Store user in request context
            g.user = validation['user']
            g.tier = validation['tier']
            g.validation = validation
            
            # Check if request is allowed
            if not validation['allowed']:
                return APIResponse.error(
                    message=validation['message'],
                    error='TierLimitExceeded',
                    status_code=402,  # Payment Required
                    upgrade_url=validation.get('upgrade_url'),
                    suggested_tier=validation.get('suggested_tier'),
                    current_tier=validation['tier'],
                    daily_usage=f"{validation['daily_requests_used']}/{validation['daily_requests_limit']}"
                )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def optional_auth():
    """
    Decorator for optional authentication (for free endpoints)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get API key from header or query parameter
            api_key = request.headers.get('X-API-Key') or \
                     request.headers.get('Authorization') or \
                     request.args.get('api_key')
            
            # Extract Bearer token if present
            if api_key and api_key.startswith('Bearer '):
                api_key = api_key[7:]
            
            # Get user if API key is provided
            if api_key:
                user = user_manager.get_user_by_api_key(api_key)
                if user:
                    g.user = user
                    g.tier = user.tier
            
            # If no API key, use anonymous user
            if not hasattr(g, 'user'):
                g.user = user_manager.users.get('anonymous')
                g.tier = 'free'
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator