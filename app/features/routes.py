"""
Premium feature endpoints
"""
from flask import Blueprint, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import swag_from

from app.features.summarizer import summarizer
from app.features.keyword_extractor import keyword_extractor
from app.utils.response import APIResponse

bp = Blueprint('features', __name__)
limiter = Limiter(key_func=get_remote_address)

@bp.route('/summarize', methods=['POST'])
@limiter.limit("50 per hour")  # Premium feature - stricter limits
@swag_from({
    'tags': ['Premium Features'],
    'description': 'Summarize text using extractive summarization',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'required': ['text'],
            'properties': {
                'text': {
                    'type': 'string',
                    'description': 'Text to summarize',
                    'example': 'Natural language processing is a field of artificial intelligence that focuses on the interaction between computers and human language.'
                },
                'sentences': {
                    'type': 'integer',
                    'minimum': 1,
                    'maximum': 10,
                    'default': 3,
                    'description': 'Number of sentences in summary'
                }
            }
        }
    }],
    'responses': {
        200: {'description': 'Success'},
        400: {'description': 'Bad Request'}
    }
})
def summarize_text():
    """Summarize text endpoint"""
    import time
    start_time = time.time()
    
    data = request.get_json()
    
    if not data or 'text' not in data:
        return APIResponse.error(
            message="Missing 'text' field in request body",
            status_code=400
        )
    
    text = data.get('text', '').strip()
    sentences = data.get('sentences', 3)
    
    if not text:
        return APIResponse.error(
            message="Text cannot be empty",
            status_code=400
        )
    
    if len(text) > 5000:  # Limit for summarization
        return APIResponse.error(
            message="Text exceeds maximum length of 5000 characters for summarization",
            status_code=400
        )
    
    try:
        # Generate summary
        result = summarizer.summarize(text, sentences)
        
        processing_time = round((time.time() - start_time) * 1000, 2)
        
        response_data = {
            'original': text[:200] + '...' if len(text) > 200 else text,
            'summary': result['summary'],
            'metrics': {
                'reduction_percent': result['reduction_percent'],
                'original_sentences': result['original_sentences'],
                'summary_sentences': result['summary_sentences'],
                'original_words': result.get('original_word_count', len(text.split())),
                'summary_words': result.get('summary_word_count', len(result['summary'].split())),
                'processing_time_ms': processing_time
            }
        }
        
        # Add note if present
        if 'note' in result:
            response_data['note'] = result['note']
        
        return APIResponse.success(
            data=response_data,
            message="Text summarized successfully"
        )
        
    except Exception as e:
        return APIResponse.error(
            message="Failed to summarize text",
            error=str(e),
            status_code=500
        )

@bp.route('/keywords', methods=['POST'])
@limiter.limit("50 per hour")
@swag_from({
    'tags': ['Premium Features'],
    'description': 'Extract keywords from text with importance scoring',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'required': ['text'],
            'properties': {
                'text': {
                    'type': 'string',
                    'description': 'Text to extract keywords from',
                    'example': 'Machine learning algorithms improve their performance as they are exposed to more data over time.'
                },
                'top_n': {
                    'type': 'integer',
                    'minimum': 1,
                    'maximum': 20,
                    'default': 10,
                    'description': 'Number of top keywords to extract'
                }
            }
        }
    }],
    'responses': {
        200: {'description': 'Success'},
        400: {'description': 'Bad Request'}
    }
})
def extract_keywords():
    """Extract keywords from text"""
    import time
    start_time = time.time()
    
    data = request.get_json()
    
    if not data or 'text' not in data:
        return APIResponse.error(
            message="Missing 'text' field in request body",
            status_code=400
        )
    
    text = data.get('text', '').strip()
    top_n = data.get('top_n', 10)
    
    if not text:
        return APIResponse.error(
            message="Text cannot be empty",
            status_code=400
        )
    
    if len(text) > 5000:  # Limit for keyword extraction
        return APIResponse.error(
            message="Text exceeds maximum length of 5000 characters for keyword extraction",
            status_code=400
        )
    
    try:
        # Extract keywords
        result = keyword_extractor.extract_keywords(text, top_n)
        
        processing_time = round((time.time() - start_time) * 1000, 2)
        
        response_data = {
            'original': text[:200] + '...' if len(text) > 200 else text,
            'keywords': result['keywords'],
            'metrics': {
                'total_keywords_found': result['total_keywords_found'],
                'text_complexity': result['text_complexity'],
                'words_analyzed': result['total_words_analyzed'],
                'processing_time_ms': processing_time
            }
        }
        
        return APIResponse.success(
            data=response_data,
            message="Keywords extracted successfully"
        )
        
    except Exception as e:
        return APIResponse.error(
            message="Failed to extract keywords",
            error=str(e),
            status_code=500
        )

@bp.route('/features', methods=['GET'])
def list_features():
    """List all available premium features"""
    return APIResponse.success(
        data={
            'premium_features': [
                {
                    'name': 'Text Summarization',
                    'endpoint': '/summarize',
                    'method': 'POST',
                    'description': 'Generate concise summaries of long texts',
                    'parameters': ['text', 'sentences'],
                    'limits': '50 requests/hour'
                },
                {
                    'name': 'Keyword Extraction',
                    'endpoint': '/keywords',
                    'method': 'POST',
                    'description': 'Extract important keywords with importance scores',
                    'parameters': ['text', 'top_n'],
                    'limits': '50 requests/hour'
                }
            ],
            'upcoming_features': [
                'Grammar Checking',
                'Plagiarism Detection',
                'Text Classification',
                'Named Entity Recognition'
            ]
        },
        message="Premium features available"
    )