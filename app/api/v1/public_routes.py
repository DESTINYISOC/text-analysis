# Complete public_routes.py
from flask import Blueprint, jsonify
from app.config import Config

bp = Blueprint('public_api', __name__)

@bp.route('/pricing', methods=['GET'])
def pricing_page():
    """Public pricing information for potential customers"""
    return jsonify({
        'success': True,
        'service': 'Text Augmentation API',
        'description': 'Advanced NLP API for text enrichment, sentiment analysis, and content augmentation',
        'pricing_tiers': {
            'free': {
                'monthly': 0,
                'yearly': 0,
                'savings': '0%',
                'features': [
                    '100 requests per day',
                    'Basic sentiment analysis',
                    'Up to 3 text augmentations',
                    'Single text processing'
                ]
            },
            'basic': {
                'monthly': 9.99,
                'yearly': 99.99,
                'savings': '16%',
                'features': [
                    '1,000 requests per day',
                    'Advanced sentiment + tone analysis',
                    'Up to 10 text augmentations',
                    'Batch processing (10 texts)',
                    'Priority support'
                ]
            },
            'pro': {
                'monthly': 29.99,
                'yearly': 299.99,
                'savings': '16%',
                'features': [
                    '10,000 requests per day',
                    'All Basic features',
                    'Text summarization',
                    'Keyword extraction',
                    'Batch processing (100 texts)',
                    'Email support'
                ]
            },
            'enterprise': {
                'monthly': 99.99,
                'yearly': 999.99,
                'savings': '16%',
                'features': [
                    'Unlimited requests',
                    'All Pro features',
                    'Custom model training',
                    'Dedicated support',
                    'SLA guarantee',
                    'White-label options'
                ]
            }
        },
        'endpoints': {
            'free': ['/enrich/text', '/analyze/sentiment'],
            'basic': ['/enrich/text', '/analyze/sentiment', '/enrich/two'],
            'pro': ['/enrich/text', '/analyze/sentiment', '/enrich/batch', '/summarize', '/keywords'],
            'enterprise': 'All endpoints + custom endpoints'
        },
        'contact': {
            'sales': 'sales@yourapi.com',
            'support': 'support@yourapi.com',
            'website': 'https://yourapi.com'
        }
    })

@bp.route('/features', methods=['GET'])
def features_page():
    """Detailed features list"""
    return jsonify({
        'success': True,
        'features': {
            'core_nlp': [
                'Sentiment Analysis with polarity (-1 to +1) and subjectivity scores',
                'Text Augmentation with intelligent synonym replacement',
                'Grammatical coherence preservation',
                'Tone detection (formal, informal, excited, questioning)',
                'Part-of-speech tagging'
            ],
            'advanced_features': [
                'Batch processing for multiple texts in parallel',
                'Text summarization (extractive method)',
                'Keyword extraction with TF scoring',
                'Language detection',
                'Readability scoring'
            ],
            'api_features': [
                'RESTful JSON API with consistent response format',
                'Rate limiting per subscription tier',
                'API key authentication',
                'Interactive Swagger documentation',
                'Webhook support for async processing',
                'Comprehensive error handling'
            ],
            'developer_experience': [
                'Clean, consistent JSON responses',
                'Detailed error messages',
                'Comprehensive documentation',
                'Code examples in multiple languages',
                'SDK libraries (Python, JavaScript)'
            ]
        }
    })

@bp.route('/quickstart', methods=['GET'])
def quickstart_guide():
    """Quick start guide for developers"""
    return jsonify({
        'success': True,
        'quickstart': [
            '1. Sign up at https://yourapi.com/signup to get your API key',
            '2. Test the API with your free tier (100 requests/day)',
            '3. Use the interactive docs at /api/docs/ to explore endpoints',
            '4. Integrate into your application using the code examples below'
        ],
        'code_examples': {
            'python': {
                'sentiment_analysis': '''
import requests

api_key = "your_api_key_here"
url = "https://api.yourapi.com/v1/analyze/sentiment"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

data = {"text": "I love this amazing product!"}
response = requests.post(url, json=data, headers=headers)
print(response.json())'''
            },
            'javascript': {
                'text_augmentation': '''
const apiKey = "your_api_key_here";
const url = "https://api.yourapi.com/v1/enrich/text";

const data = {
  text: "The quick brown fox jumps over the lazy dog.",
  augmentation_count: 3
};

fetch(url, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${apiKey}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify(data)
})
.then(response => response.json())
.then(data => console.log(data));'''
            }
        }
    })