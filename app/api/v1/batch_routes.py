"""
Batch processing endpoints for multiple texts with tier enforcement
"""
from flask import Blueprint, request, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import swag_from
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from app.core.augmentor import augmentor
from app.core.validator import validate_enrich_request
from app.auth.middleware import require_auth
from app.utils.response import APIResponse
from app.auth.models import user_manager

bp = Blueprint('batch_api', __name__)
limiter = Limiter(key_func=get_remote_address)

def process_single_text(item, user_tier='free'):
    """Process a single text item with tier limits"""
    text_data = item.get('text', '')
    augmentation_count = item.get('augmentation_count', 3)
    
    try:
        # Apply tier limits to augmentation count
        tier_limits = user_manager.users['anonymous'].get_tier_limits() if user_tier == 'free' else \
                     next((u.get_tier_limits() for u in user_manager.users.values() if u.tier == user_tier), 
                          user_manager.users['anonymous'].get_tier_limits())
        
        max_allowed = tier_limits['max_augmentations']
        if augmentation_count > max_allowed:
            augmentation_count = max_allowed
        
        # Use the correct augmentation method
        sentiment = augmentor.analyze_sentiment(text_data)
        augmentations = augmentor.augment_text_with_grammar(text_data, augmentation_count)
        replaceable_words = augmentor.find_replaceable_words(text_data)
        
        return {
            'success': True,
            'original': text_data,
            'sentiment': sentiment,
            'augmentations': augmentations,
            'metadata': {
                'word_count': len(text_data.split()),
                'replaceable_words': len(replaceable_words),
                'augmentation_count': len(augmentations),
                'requested_augmentations': item.get('augmentation_count', 3),
                'allowed_augmentations': augmentation_count,
                'augmentation_limited': item.get('augmentation_count', 3) > augmentation_count
            }
        }
    except Exception as e:
        return {
            'success': False,
            'original': text_data,
            'error': str(e),
            'error_type': type(e).__name__
        }

@bp.route('/enrich/two', methods=['POST'])
@limiter.limit("50 per hour")
@require_auth(feature='batch')
@swag_from({
    'tags': ['Batch Processing'],
    'description': '''
    Process exactly two texts in parallel.
    
    **Tier Limits:**
    - Free: Not available
    - Basic: Up to 10 texts per batch
    - Pro: Up to 100 texts per batch
    - Enterprise: Up to 1000 texts per batch
    
    Batch processing is a premium feature.
    ''',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'required': ['texts'],
            'properties': {
                'texts': {
                    'type': 'array',
                    'minItems': 2,
                    'maxItems': 2,
                    'items': {
                        'type': 'object',
                        'required': ['text'],
                        'properties': {
                            'text': {
                                'type': 'string',
                                'description': 'Text to process'
                            },
                            'augmentation_count': {
                                'type': 'integer',
                                'minimum': 1,
                                'maximum': 50,
                                'default': 3,
                                'description': 'Number of augmentations per text'
                            }
                        }
                    }
                }
            }
        }
    }, {
        'name': 'X-API-Key',
        'in': 'header',
        'type': 'string',
        'required': True,
        'description': 'API key (batch processing requires authentication)'
    }],
    'responses': {
        200: {
            'description': 'Success',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'results': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'success': {'type': 'boolean'},
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
                                                'augmentation_count': {'type': 'integer'},
                                                'requested_augmentations': {'type': 'integer'},
                                                'allowed_augmentations': {'type': 'integer'},
                                                'augmentation_limited': {'type': 'boolean'}
                                            }
                                        }
                                    }
                                }
                            },
                            'batch_metadata': {
                                'type': 'object',
                                'properties': {
                                    'text_count': {'type': 'integer'},
                                    'successful_count': {'type': 'integer'},
                                    'failed_count': {'type': 'integer'},
                                    'processing_time_ms': {'type': 'number'},
                                    'parallel_processing': {'type': 'boolean'},
                                    'user_tier': {'type': 'string'},
                                    'batch_limit_exceeded': {'type': 'boolean'},
                                    'upgrade_suggestion': {
                                        'type': 'object',
                                        'properties': {
                                            'message': {'type': 'string'},
                                            'current_limit': {'type': 'integer'},
                                            'suggested_tier': {'type': 'string'},
                                            'upgrade_url': {'type': 'string'}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        400: {'description': 'Bad Request'},
        402: {
            'description': 'Payment Required - batch processing not available for free tier',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': False},
                    'error': {'type': 'string'},
                    'message': {'type': 'string'},
                    'current_tier': {'type': 'string'},
                    'required_tier': {'type': 'string'},
                    'upgrade_url': {'type': 'string'}
                }
            }
        }
    }
})
def enrich_two_texts():
    """Process exactly two texts (premium feature)"""
    # Check if user tier allows batch processing
    user = g.user
    user_tier = g.tier
    
    if user_tier == 'free':
        return APIResponse.tier_limit_error(
            message='Batch processing is not available in the Free tier.',
            current_tier=user_tier,
            suggested_tier='basic',
            required_tier='basic',
            limit_details={
                'feature': 'batch_processing',
                'allowed': False,
                'message': 'Upgrade to Basic tier or higher for batch processing'
            }
        )
    
    start_time = time.time()
    data = request.get_json()
    
    if not data or 'texts' not in data:
        return APIResponse.error(
            message="Missing 'texts' array in request body",
            status_code=400
        )
    
    texts = data['texts']
    if not isinstance(texts, list) or len(texts) != 2:
        return APIResponse.error(
            message="Must provide exactly 2 text objects in 'texts' array",
            status_code=400
        )
    
    # Validate each text item
    for i, item in enumerate(texts):
        if not isinstance(item, dict) or 'text' not in item:
            return APIResponse.error(
                message=f"Text item {i+1} must be an object with a 'text' field",
                status_code=400
            )
        
        text = item.get('text', '').strip()
        if not text:
            return APIResponse.error(
                message=f"Text item {i+1} cannot be empty",
                status_code=400
            )
    
    # Check batch size against tier limits
    tier_limits = user.get_tier_limits()
    if len(texts) > tier_limits['batch_limit']:
        return APIResponse.tier_limit_error(
            message=f'{user_tier.capitalize()} tier allows maximum {tier_limits["batch_limit"]} texts per batch. You requested {len(texts)}.',
            current_tier=user_tier,
            suggested_tier='pro' if len(texts) > 10 else 'enterprise',
            limit_details={
                'requested': len(texts),
                'allowed': tier_limits['batch_limit'],
                'feature': 'batch_size'
            }
        )
    
    # Process in parallel
    results = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit all tasks
        future_to_item = {executor.submit(process_single_text, item, user_tier): item for item in texts}
        
        # Collect results as they complete
        for future in as_completed(future_to_item):
            results.append(future.result())
    
    processing_time = round((time.time() - start_time) * 1000, 2)
    
    # Calculate success rate
    successful = sum(1 for r in results if r.get('success', False))
    failed = len(results) - successful
    
    # Check if any augmentations were limited
    augmentation_limited = any(
        r.get('success', False) and 
        r.get('metadata', {}).get('augmentation_limited', False) 
        for r in results
    )
    
    # Prepare response
    response_data = {
        'results': results,
        'batch_metadata': {
            'text_count': 2,
            'successful_count': successful,
            'failed_count': failed,
            'processing_time_ms': processing_time,
            'parallel_processing': True,
            'user_tier': user_tier,
            'batch_limit': tier_limits['batch_limit'],
            'average_time_per_text': round(processing_time / len(texts), 2),
            'success_rate': round(successful / len(texts) * 100, 2) if texts else 0
        }
    }
    
    # Add upgrade suggestion if augmentations were limited
    if augmentation_limited and user_tier == 'basic':
        max_requested = max(
            r.get('metadata', {}).get('requested_augmentations', 3) 
            for r in results if r.get('success', False)
        )
        
        response_data['batch_metadata']['upgrade_suggestion'] = {
            'message': f'Some texts requested more than 10 augmentations. Basic tier limited to 10.',
            'current_limit': 10,
            'suggested_tier': 'pro',
            'upgrade_url': '/api/v1/pricing',
            'features_unlocked': [
                'Up to 50 augmentations per text',
                'Higher batch limits',
                'Priority processing',
                'All premium features'
            ]
        }
    
    return APIResponse.success(
        data=response_data,
        message=f"2 texts processed successfully ({successful} successful, {failed} failed)"
    )

@bp.route('/enrich/three', methods=['POST'])
@limiter.limit("40 per hour")
@require_auth(feature='batch')
def enrich_three_texts():
    """Process exactly three texts (premium feature)"""
    # Check if user tier allows batch processing
    user = g.user
    user_tier = g.tier
    
    if user_tier == 'free':
        return APIResponse.tier_limit_error(
            message='Batch processing is not available in the Free tier.',
            current_tier=user_tier,
            suggested_tier='basic',
            required_tier='basic',
            limit_details={
                'feature': 'batch_processing',
                'allowed': False,
                'message': 'Upgrade to Basic tier or higher for batch processing'
            }
        )
    
    start_time = time.time()
    data = request.get_json()
    
    if not data or 'texts' not in data:
        return APIResponse.error(
            message="Missing 'texts' array in request body",
            status_code=400
        )
    
    texts = data['texts']
    if not isinstance(texts, list) or len(texts) != 3:
        return APIResponse.error(
            message="Must provide exactly 3 text objects in 'texts' array",
            status_code=400
        )
    
    # Validate each text item
    for i, item in enumerate(texts):
        if not isinstance(item, dict) or 'text' not in item:
            return APIResponse.error(
                message=f"Text item {i+1} must be an object with a 'text' field",
                status_code=400
            )
        
        text = item.get('text', '').strip()
        if not text:
            return APIResponse.error(
                message=f"Text item {i+1} cannot be empty",
                status_code=400
            )
    
    # Check batch size against tier limits
    tier_limits = user.get_tier_limits()
    if len(texts) > tier_limits['batch_limit']:
        return APIResponse.tier_limit_error(
            message=f'{user_tier.capitalize()} tier allows maximum {tier_limits["batch_limit"]} texts per batch. You requested {len(texts)}.',
            current_tier=user_tier,
            suggested_tier='pro' if len(texts) > 10 else 'enterprise',
            limit_details={
                'requested': len(texts),
                'allowed': tier_limits['batch_limit'],
                'feature': 'batch_size'
            }
        )
    
    # Process in parallel
    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all tasks
        future_to_item = {executor.submit(process_single_text, item, user_tier): item for item in texts}
        
        # Collect results as they complete
        for future in as_completed(future_to_item):
            results.append(future.result())
    
    processing_time = round((time.time() - start_time) * 1000, 2)
    
    # Calculate success rate
    successful = sum(1 for r in results if r.get('success', False))
    failed = len(results) - successful
    
    # Prepare response
    response_data = {
        'results': results,
        'batch_metadata': {
            'text_count': 3,
            'successful_count': successful,
            'failed_count': failed,
            'processing_time_ms': processing_time,
            'parallel_processing': True,
            'user_tier': user_tier,
            'batch_limit': tier_limits['batch_limit'],
            'average_time_per_text': round(processing_time / len(texts), 2),
            'success_rate': round(successful / len(texts) * 100, 2) if texts else 0
        }
    }
    
    return APIResponse.success(
        data=response_data,
        message=f"3 texts processed successfully ({successful} successful, {failed} failed)"
    )

@bp.route('/enrich/batch', methods=['POST'])
@limiter.limit("30 per hour")
@require_auth(feature='batch')
@swag_from({
    'tags': ['Batch Processing'],
    'description': '''
    Process multiple texts (1-100) in parallel.
    
    **Tier Limits:**
    - Basic: 1-10 texts per batch
    - Pro: 1-100 texts per batch
    - Enterprise: 1-1000 texts per batch
    
    Free tier does not include batch processing.
    ''',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'required': ['texts'],
            'properties': {
                'texts': {
                    'type': 'array',
                    'minItems': 1,
                    'maxItems': 100,
                    'items': {
                        'type': 'object',
                        'required': ['text'],
                        'properties': {
                            'text': {'type': 'string'},
                            'augmentation_count': {
                                'type': 'integer',
                                'minimum': 1,
                                'maximum': 50,
                                'default': 3,
                                'description': 'Number of augmentations per text (tier-limited)'
                            }
                        }
                    }
                }
            }
        }
    }, {
        'name': 'X-API-Key',
        'in': 'header',
        'type': 'string',
        'required': True,
        'description': 'API key (batch processing requires authentication)'
    }],
    'responses': {
        200: {'description': 'Success'},
        400: {'description': 'Bad Request'},
        402: {'description': 'Payment Required - tier limit exceeded'}
    }
})
def enrich_multiple_texts():
    """Process 1-100 texts in parallel (premium feature)"""
    # Check if user tier allows batch processing
    user = g.user
    user_tier = g.tier
    
    if user_tier == 'free':
        return APIResponse.tier_limit_error(
            message='Batch processing is not available in the Free tier.',
            current_tier=user_tier,
            suggested_tier='basic',
            required_tier='basic',
            limit_details={
                'feature': 'batch_processing',
                'allowed': False,
                'message': 'Upgrade to Basic tier or higher for batch processing'
            }
        )
    
    start_time = time.time()
    data = request.get_json()
    
    if not data or 'texts' not in data:
        return APIResponse.error(
            message="Missing 'texts' array in request body",
            status_code=400
        )
    
    texts = data['texts']
    if not isinstance(texts, list) or len(texts) < 1:
        return APIResponse.error(
            message="Must provide at least 1 text object in 'texts' array",
            status_code=400
        )
    
    # Get tier limits
    tier_limits = user.get_tier_limits()
    max_batch_size = tier_limits['batch_limit']
    
    # Check batch size against tier limits
    if len(texts) > max_batch_size:
        return APIResponse.tier_limit_error(
            message=f'{user_tier.capitalize()} tier allows maximum {max_batch_size} texts per batch. You requested {len(texts)}.',
            current_tier=user_tier,
            suggested_tier='pro' if len(texts) > 10 else 'enterprise',
            limit_details={
                'requested': len(texts),
                'allowed': max_batch_size,
                'feature': 'batch_size'
            }
        )
    
    # Validate each text item
    for i, item in enumerate(texts):
        if not isinstance(item, dict) or 'text' not in item:
            return APIResponse.error(
                message=f"Text item {i+1} must be an object with a 'text' field",
                status_code=400
            )
        
        text = item.get('text', '').strip()
        if not text:
            return APIResponse.error(
                message=f"Text item {i+1} cannot be empty",
                status_code=400
            )
        
        # Check text length against tier limits
        if len(text) > tier_limits['max_text_length']:
            return APIResponse.tier_limit_error(
                message=f'Text {i+1} exceeds {user_tier} tier character limit of {tier_limits["max_text_length"]}.',
                current_tier=user_tier,
                suggested_tier='pro' if len(text) > 2000 else 'basic',
                limit_details={
                    'text_index': i,
                    'text_length': len(text),
                    'allowed_length': tier_limits['max_text_length'],
                    'feature': 'text_length'
                }
            )
    
    # Process in parallel (limit concurrent workers based on batch size)
    max_workers = min(4, len(texts))
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_item = {executor.submit(process_single_text, item, user_tier): item for item in texts}
        
        # Collect results as they complete
        for future in as_completed(future_to_item):
            results.append(future.result())
    
    processing_time = round((time.time() - start_time) * 1000, 2)
    
    # Calculate statistics
    successful = sum(1 for r in results if r.get('success', False))
    failed = len(texts) - successful
    
    # Check for limited augmentations
    limited_augmentations = sum(
        1 for r in results 
        if r.get('success', False) and 
        r.get('metadata', {}).get('augmentation_limited', False)
    )
    
    # Calculate average processing time per successful text
    successful_times = []
    for r in results:
        if r.get('success', False):
            # Estimate processing time based on text length
            text_len = len(r.get('original', ''))
            successful_times.append(text_len)
    
    avg_text_length = sum(successful_times) / len(successful_times) if successful_times else 0
    
    # Prepare response
    response_data = {
        'results': results,
        'batch_metadata': {
            'text_count': len(texts),
            'successful_count': successful,
            'failed_count': failed,
            'processing_time_ms': processing_time,
            'parallel_workers': max_workers,
            'average_time_per_text': round(processing_time / len(texts), 2),
            'user_tier': user_tier,
            'tier_batch_limit': max_batch_size,
            'success_rate': round(successful / len(texts) * 100, 2) if texts else 0,
            'limited_augmentations_count': limited_augmentations,
            'average_text_length': round(avg_text_length, 2),
            'total_characters_processed': sum(len(r.get('original', '')) for r in results if r.get('success', False))
        }
    }
    
    # Add upgrade suggestions if needed
    upgrade_suggestions = []
    
    # Check if batch size接近 tier limit
    if len(texts) >= max_batch_size * 0.8:  # 80% of limit
        upgrade_suggestions.append({
            'type': 'batch_size',
            'message': f'You are using {len(texts)} of {max_batch_size} allowed texts. Consider upgrading for larger batches.',
            'suggested_tier': 'pro' if user_tier == 'basic' else 'enterprise'
        })
    
    # Check if augmentations were limited
    if limited_augmentations > 0 and user_tier == 'basic':
        upgrade_suggestions.append({
            'type': 'augmentation_limit',
            'message': f'{limited_augmentations} texts had augmentation counts limited to 10.',
            'suggested_tier': 'pro'
        })
    
    if upgrade_suggestions:
        response_data['batch_metadata']['upgrade_suggestions'] = upgrade_suggestions
    
    # Add efficiency metrics for large batches
    if len(texts) > 5:
        serial_estimate = processing_time * len(texts)  # Very rough estimate
        efficiency_gain = round((1 - processing_time / serial_estimate) * 100, 2) if serial_estimate > 0 else 0
        response_data['batch_metadata']['efficiency_metrics'] = {
            'estimated_serial_time_ms': round(serial_estimate, 2),
            'parallel_efficiency_gain': efficiency_gain,
            'time_saved_ms': round(max(0, serial_estimate - processing_time), 2)
        }
    
    return APIResponse.success(
        data=response_data,
        message=f"Batch of {len(texts)} texts processed ({successful} successful, {failed} failed)"
    )

@bp.route('/batch/limits', methods=['GET'])
@require_auth(feature='batch')
def batch_limits():
    """
    Get batch processing limits for current tier
    """
    user = g.user
    user_tier = g.tier
    
    if user_tier == 'free':
        return APIResponse.tier_limit_error(
            message='Batch processing information requires at least Basic tier.',
            current_tier=user_tier,
            suggested_tier='basic',
            required_tier='basic'
        )
    
    tier_limits = user.get_tier_limits()
    
    return APIResponse.success(
        data={
            'tier': user_tier,
            'batch_limits': {
                'max_batch_size': tier_limits['batch_limit'],
                'max_augmentations_per_text': tier_limits['max_augmentations'],
                'max_text_length': tier_limits['max_text_length'],
                'daily_request_limit': tier_limits['daily_requests']
            },
            'recommended_usage': {
                'small_batches': f'1-{min(5, tier_limits["batch_limit"])} texts for quick processing',
                'medium_batches': f'{min(6, tier_limits["batch_limit"])}-{min(20, tier_limits["batch_limit"])} texts for moderate workloads',
                'large_batches': f'{min(21, tier_limits["batch_limit"])}-{tier_limits["batch_limit"]} texts for bulk processing'
            } if tier_limits['batch_limit'] > 5 else {},
            'performance_tips': [
                f'Use 2-4 parallel workers for optimal performance',
                'Keep individual texts under 1000 characters for faster processing',
                'Monitor your daily request limit: {}/{} remaining today'.format(
                    max(0, tier_limits['daily_requests'] - user.daily_requests.get(time.strftime('%Y-%m-%d'), 0)),
                    tier_limits['daily_requests']
                )
            ]
        },
        message=f"Batch processing limits for {user_tier} tier"
    )