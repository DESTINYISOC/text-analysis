"""
API v1 Routes
"""
from flask import Blueprint, request, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import swag_from
import time

from app.core.augmentor import augmentor
from app.core.validator import validate_enrich_request
from app.auth.middleware import require_auth, optional_auth
from app.utils.response import APIResponse
from app.auth.models import user_manager

bp = Blueprint('api_v1', __name__)
limiter = Limiter(key_func=get_remote_address)

def get_daily_requests_remaining(user):
    """Calculate daily requests remaining for user"""
    from datetime import datetime
    today = datetime.utcnow().date().isoformat()
    daily_used = user.daily_requests.get(today, 0)
    daily_limit = user.get_tier_limits()['daily_requests']
    return max(0, daily_limit - daily_used)

@bp.route('/enrich/text', methods=['POST'])
@limiter.limit("100 per hour")
@require_auth(feature='enrich_text')
@swag_from({
    'tags': ['Text Processing'],
    'description': '''
    Enrich text with sentiment analysis and intelligent synonym replacements.
    
    This endpoint analyzes the sentiment of the input text and generates
    multiple versions with synonyms replacing non-critical words.
    
    **Tier Limits:**
    - Free: 3 augmentations max, 100 requests/day
    - Basic: 10 augmentations max, 1000 requests/day  
    - Pro: 50 augmentations max, 10000 requests/day
    - Enterprise: 200 augmentations max, unlimited requests
    ''',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['text'],
                'properties': {
                    'text': {
                        'type': 'string',
                        'description': 'The text to enrich',
                        'example': 'The beautiful sunset over the calm ocean was absolutely breathtaking.'
                    },
                    'augmentation_count': {
                        'type': 'integer',
                        'minimum': 1,
                        'maximum': 200,
                        'default': 3,
                        'description': 'Number of synonym-augmented sentences to generate'
                    }
                }
            }
        },
        {
            'name': 'X-API-Key',
            'in': 'header',
            'type': 'string',
            'required': False,
            'description': 'API key for authenticated requests (optional for free tier)'
        }
    ],
    'responses': {
        200: {
            'description': 'Successful enrichment',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'original': {'type': 'string'},
                            'sentiment': {
                                'type': 'object',
                                'properties': {
                                    'polarity': {'type': 'number'},
                                    'subjectivity': {'type': 'number'},
                                    'label': {'type': 'string'},
                                    'emoji': {'type': 'string'},
                                    'confidence': {'type': 'number'}
                                }
                            },
                            'augmentations': {
                                'type': 'array',
                                'items': {'type': 'string'}
                            },
                            'metadata': {
                                'type': 'object',
                                'properties': {
                                    'word_count': {'type': 'integer'},
                                    'replaceable_words': {'type': 'integer'},
                                    'processing_time_ms': {'type': 'number'},
                                    'augmentation_count': {'type': 'integer'},
                                    'user_tier': {'type': 'string'},
                                    'daily_requests_remaining': {'type': 'integer'},
                                    'daily_requests_used': {'type': 'integer'},
                                    'daily_requests_limit': {'type': 'integer'}
                                }
                            },
                            'upgrade_suggestion': {
                                'type': 'object',
                                'properties': {
                                    'message': {'type': 'string'},
                                    'requested': {'type': 'integer'},
                                    'allowed': {'type': 'integer'},
                                    'upgrade_url': {'type': 'string'},
                                    'suggested_tier': {'type': 'string'}
                                }
                            }
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Bad request - invalid input',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': False},
                    'error': {'type': 'string'},
                    'message': {'type': 'string'}
                }
            }
        },
        402: {
            'description': 'Payment required - tier limit exceeded',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': False},
                    'error': {'type': 'string'},
                    'message': {'type': 'string'},
                    'current_tier': {'type': 'string'},
                    'suggested_tier': {'type': 'string'},
                    'upgrade_url': {'type': 'string'},
                    'daily_usage': {'type': 'string'}
                }
            }
        },
        429: {
            'description': 'Too many requests'
        }
    }
})
def enrich_text():
    """
    Main text enrichment endpoint with tier enforcement
    """
    start_time = time.time()
    
    # Get and validate input
    data = request.get_json()
    if not data:
        return APIResponse.error(
            message="No JSON data provided",
            status_code=400
        )
    
    # Validate request
    validation_result = validate_enrich_request(data)
    if not validation_result['valid']:
        return APIResponse.error(
            message=validation_result['message'],
            errors=validation_result.get('errors'),
            status_code=400
        )
    
    # Extract parameters
    text = data.get('text', '').strip()
    requested_augmentation_count = data.get('augmentation_count', 3)
    
    # Get user from authentication middleware (set by @require_auth)
    user = g.user
    user_tier = g.tier
    
    # Check tier limits
    tier_limits = user.get_tier_limits()
    max_allowed_augmentations = tier_limits['max_augmentations']
    
    # Enforce augmentation limit
    if requested_augmentation_count > max_allowed_augmentations:
        # For free tier: silently downgrade to max allowed
        # For paid tiers: inform user they exceeded their plan limit
        if user_tier == 'free':
            actual_augmentation_count = max_allowed_augmentations  # Force to 3
            augmentation_limited = True
        else:
            # Paid users get an error if they exceed their plan
            return APIResponse.tier_limit_error(
                message=f'{user_tier.capitalize()} tier allows maximum {max_allowed_augmentations} augmentations. You requested {requested_augmentation_count}.',
                current_tier=user_tier,
                suggested_tier='pro' if requested_augmentation_count > 10 else 'enterprise',
                limit_details={
                    'requested': requested_augmentation_count,
                    'allowed': max_allowed_augmentations,
                    'feature': 'augmentation_count'
                }
            )
    else:
        actual_augmentation_count = requested_augmentation_count
        augmentation_limited = False
    
    try:
        # Analyze sentiment
        sentiment = augmentor.analyze_sentiment(text)
        
        # Generate augmentations with grammatical coherence
        augmentations = augmentor.augment_text_with_grammar(text, actual_augmentation_count)
        
        # Find replaceable words for metadata
        replaceable_words = augmentor.find_replaceable_words(text)
        
        # Calculate processing time
        processing_time = round((time.time() - start_time) * 1000, 2)
        
        # Get daily usage stats
        today = time.strftime('%Y-%m-%d')
        daily_used = user.daily_requests.get(today, 0)
        daily_limit = tier_limits['daily_requests']
        daily_remaining = get_daily_requests_remaining(user)
        
        # Prepare response
        response_data = {
            'original': text,
            'sentiment': sentiment,
            'augmentations': augmentations,
            'metadata': {
                'word_count': len(text.split()),
                'replaceable_words': len(replaceable_words),
                'processing_time_ms': processing_time,
                'augmentation_count': len(augmentations),
                'user_tier': user_tier,
                'daily_requests_remaining': daily_remaining,
                'daily_requests_used': daily_used,
                'daily_requests_limit': daily_limit,
                'max_augmentations_allowed': max_allowed_augmentations,
                'requested_augmentations': requested_augmentation_count
            }
        }
        
        # Add upgrade suggestion if augmentation was limited for free tier
        if augmentation_limited and user_tier == 'free':
            response_data['upgrade_suggestion'] = {
                'message': f'Free tier limited to {max_allowed_augmentations} augmentations. You requested {requested_augmentation_count}.',
                'requested': requested_augmentation_count,
                'allowed': max_allowed_augmentations,
                'upgrade_url': '/api/v1/pricing',
                'suggested_tier': 'basic' if requested_augmentation_count <= 10 else 'pro',
                'features_unlocked': [
                    f'Up to {10 if requested_augmentation_count <= 10 else 50} augmentations',
                    'Higher daily request limits',
                    'Batch processing capabilities',
                    'Priority support' if requested_augmentation_count > 10 else 'Email support'
                ]
            }
        
        # Add warning if接近 daily limit
        if daily_remaining <= 10 and daily_remaining > 0:
            response_data['daily_limit_warning'] = {
                'message': f'You have {daily_remaining} requests remaining today.',
                'remaining': daily_remaining,
                'limit': daily_limit
            }
        
        return APIResponse.success(
            data=response_data,
            message="Text enriched successfully"
        )
        
    except Exception as e:
        return APIResponse.error(
            message="Internal server error",
            error=str(e),
            status_code=500
        )

@bp.route('/account/info', methods=['GET'])
@optional_auth()
def account_info():
    """
    Get current user account information and usage statistics
    """
    user = g.user
    user_tier = g.tier
    tier_limits = user.get_tier_limits()
    
    today = time.strftime('%Y-%m-%d')
    daily_used = user.daily_requests.get(today, 0)
    daily_limit = tier_limits['daily_requests']
    
    return APIResponse.success(
        data={
            'user_id': user.user_id,
            'email': user.email,
            'tier': user_tier,
            'subscription': {
                'current_tier': user_tier,
                'subscription_start': user.subscription_start.isoformat() if user.subscription_start else None,
                'subscription_end': user.subscription_end.isoformat() if user.subscription_end else None,
                'monthly_price': tier_limits['monthly_price'],
                'yearly_price': tier_limits['yearly_price']
            },
            'usage': {
                'daily_used': daily_used,
                'daily_limit': daily_limit,
                'daily_remaining': max(0, daily_limit - daily_used),
                'total_requests': user.total_requests,
                'monthly_requests': user.monthly_requests
            },
            'limits': {
                'max_augmentations': tier_limits['max_augmentations'],
                'batch_limit': tier_limits['batch_limit'],
                'max_text_length': tier_limits['max_text_length'],
                'available_features': tier_limits['features']
            },
            'upgrade_options': [
                {
                    'tier': 'basic',
                    'monthly_price': 9.99,
                    'yearly_price': 99.99,
                    'features': ['Up to 10 augmentations', '1000 requests/day', 'Batch processing']
                },
                {
                    'tier': 'pro',
                    'monthly_price': 29.99,
                    'yearly_price': 299.99,
                    'features': ['Up to 50 augmentations', '10000 requests/day', 'All premium features']
                }
            ] if user_tier == 'free' else []
        },
        message="Account information retrieved successfully"
    )

@bp.route('/account/upgrade', methods=['POST'])
@optional_auth()
def request_upgrade():
    """
    Request to upgrade account tier
    """
    data = request.get_json() or {}
    requested_tier = data.get('tier', 'basic')
    
    user = g.user
    current_tier = g.tier
    
    # Validate requested tier
    allowed_tiers = ['basic', 'pro', 'enterprise']
    if requested_tier not in allowed_tiers:
        return APIResponse.error(
            message=f"Invalid tier. Allowed tiers: {', '.join(allowed_tiers)}",
            status_code=400
        )
    
    # Check if already at or above requested tier
    tier_levels = {'free': 0, 'basic': 1, 'pro': 2, 'enterprise': 3}
    if tier_levels.get(current_tier, 0) >= tier_levels.get(requested_tier, 0):
        return APIResponse.error(
            message=f"You are already at {current_tier} tier or higher",
            status_code=400
        )
    
    # In a real implementation, this would trigger payment processing
    # For now, we'll simulate successful upgrade
    user.upgrade_tier(requested_tier, f"sub_{time.time()}")
    
    return APIResponse.success(
        data={
            'previous_tier': current_tier,
            'new_tier': requested_tier,
            'upgraded_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'subscription_id': user.subscription_id,
            'next_billing_date': (time.time() + 30*24*60*60),  # 30 days from now
            'message': 'Upgrade successful! Payment processing would be handled here in production.'
        },
        message=f"Account upgraded from {current_tier} to {requested_tier} tier"
    )

@bp.route('/account/api-keys', methods=['GET'])
@optional_auth()
def list_api_keys():
    """
    List API keys for the current user
    """
    user = g.user
    
    # In production, you'd fetch from database
    # For now, return a mock response
    api_keys = []
    
    # Generate a sample API key if user doesn't have one
    if user.user_id != 'anonymous':
        sample_key = f"ta_{user.user_id}_{int(time.time())}"
        api_keys.append({
            'key': sample_key,
            'name': 'default',
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'last_used': time.strftime('%Y-%m-%d %H:%M:%S'),
            'request_count': user.total_requests
        })
    
    return APIResponse.success(
        data={
            'user_id': user.user_id,
            'api_keys': api_keys,
            'total_keys': len(api_keys)
        },
        message="API keys retrieved successfully"
    )

@bp.route('/usage/stats', methods=['GET'])
@optional_auth()
def usage_statistics():
    """
    Get detailed usage statistics
    """
    user = g.user
    
    # Calculate daily usage for last 7 days
    daily_stats = []
    for i in range(6, -1, -1):
        date_key = time.strftime('%Y-%m-%d', time.localtime(time.time() - i*24*60*60))
        count = user.daily_requests.get(date_key, 0)
        daily_stats.append({
            'date': date_key,
            'requests': count,
            'day': time.strftime('%a', time.localtime(time.time() - i*24*60*60))
        })
    
    # Calculate feature usage (simulated)
    feature_usage = {
        'enrich_text': int(user.total_requests * 0.6),
        'sentiment_analysis': int(user.total_requests * 0.3),
        'batch_processing': int(user.total_requests * 0.1)
    }
    
    return APIResponse.success(
        data={
            'user_id': user.user_id,
            'tier': g.tier,
            'total_requests': user.total_requests,
            'daily_stats': daily_stats,
            'feature_usage': feature_usage,
            'average_daily_requests': sum(user.daily_requests.values()) / max(1, len(user.daily_requests)),
            'peak_usage_day': max(user.daily_requests.items(), key=lambda x: x[1]) if user.daily_requests else None
        },
        message="Usage statistics retrieved successfully"
    )

@bp.route('/tier/limits', methods=['GET'])
def tier_limits():
    """
    Get tier limits for all plans
    """
    from app.auth.models import User
    
    # Create temp users to get limits
    free_user = User(user_id='temp_free', email='temp@example.com', tier='free')
    basic_user = User(user_id='temp_basic', email='temp@example.com', tier='basic')
    pro_user = User(user_id='temp_pro', email='temp@example.com', tier='pro')
    enterprise_user = User(user_id='temp_enterprise', email='temp@example.com', tier='enterprise')
    
    tiers = {
        'free': free_user.get_tier_limits(),
        'basic': basic_user.get_tier_limits(),
        'pro': pro_user.get_tier_limits(),
        'enterprise': enterprise_user.get_tier_limits()
    }
    
    return APIResponse.success(
        data={
            'tiers': tiers,
            'comparison': {
                'free': {
                    'best_for': 'Testing & evaluation',
                    'limitations': ['3 augmentations max', '500 character limit', 'No batch processing']
                },
                'basic': {
                    'best_for': 'Small projects & startups',
                    'advantages': ['10x daily limit', '10 augmentations', 'Batch processing']
                },
                'pro': {
                    'best_for': 'Production applications',
                    'advantages': ['100x daily limit', '50 augmentations', 'All premium features']
                },
                'enterprise': {
                    'best_for': 'Large scale deployments',
                    'advantages': ['Unlimited requests', 'Custom solutions', 'Dedicated support']
                }
            }
        },
        message="Tier limits retrieved successfully"
    )

# Health check endpoint (no authentication required)
@bp.route('/health', methods=['GET'])
def health_check():
    """API health check"""
    return APIResponse.success(
        data={
            'status': 'healthy',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'version': '1.0.0',
            'endpoints_available': True,
            'database_connected': True
        },
        message="Text Augmentation API is running"
    )