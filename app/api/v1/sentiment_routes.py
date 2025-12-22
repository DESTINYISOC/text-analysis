"""
Sentiment analysis-only endpoints with tier enforcement
"""
from flask import Blueprint, request, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import swag_from
from textblob import TextBlob
import re
import time
from datetime import datetime

from app.core.augmentor import augmentor
from app.auth.middleware import optional_auth, require_auth
from app.utils.response import APIResponse
from app.auth.models import user_manager

bp = Blueprint('sentiment_api', __name__)
limiter = Limiter(key_func=get_remote_address)

def detect_tone(text: str) -> str:
    """
    Detect the tone of the language
    """
    if not text or not isinstance(text, str):
        return "Neutral/Informative"
    
    text_lower = text.lower().strip()
    
    # Check for empty text
    if not text_lower:
        return "Neutral/Informative"
    
    # Question tone
    if text.strip().endswith('?'):
        question_words = ['who', 'what', 'where', 'when', 'why', 'how', 'which']
        if any(text_lower.startswith(word) for word in question_words):
            return "Direct Question"
        return "Questioning"
    
    # Exclamatory tone
    if any(c in text for c in ['!', '!!', '!!!']):
        exclamation_count = text.count('!')
        if exclamation_count > 2:
            return "Very Excited/Emphatic"
        return "Excited/Emphatic"
    
    # Formal tone indicators
    formal_words = ['respectfully', 'sincerely', 'therefore', 'however', 
                   'furthermore', 'moreover', 'consequently', 'accordingly',
                   'nevertheless', 'nonetheless', 'thus', 'hence']
    if any(word in text_lower for word in formal_words):
        return "Formal/Academic"
    
    # Informal tone indicators
    informal_words = ['lol', 'omg', 'wow', 'hey', 'dude', 'bro', 'bruh',
                     'awesome', 'cool', 'amazing', 'lit', 'fire', 'sick']
    contractions = ["can't", "won't", "don't", "isn't", "aren't", 
                   "wasn't", "wouldn't", "couldn't", "shouldn't",
                   "i'm", "you're", "he's", "she's", "it's", "we're", "they're"]
    
    if any(word in text_lower for word in informal_words) or \
       any(contraction in text_lower for contraction in contractions):
        return "Informal/Casual"
    
    # Aggressive/Argumentative tone
    aggressive_words = ['never', 'always', 'worst', 'terrible', 'horrible',
                       'ridiculous', 'absurd', 'nonsense', 'bullshit']
    if any(word in text_lower for word in aggressive_words):
        return "Aggressive/Argumentative"
    
    # Grateful/Appreciative tone
    grateful_words = ['thank', 'thanks', 'appreciate', 'grateful', 'blessed',
                     'helpful', 'kind', 'generous', 'supportive']
    if any(word in text_lower for word in grateful_words):
        return "Grateful/Appreciative"
    
    # Sad/Disappointed tone
    sad_words = ['sad', 'disappointed', 'unhappy', 'miserable', 'depressed',
                'regret', 'sorry', 'unfortunate', 'tragic']
    if any(word in text_lower for word in sad_words):
        return "Sad/Disappointed"
    
    # Neutral/Default
    return "Neutral/Informative"

def get_emotion_intensity(polarity: float) -> str:
    """Get emotion intensity based on polarity score"""
    abs_polarity = abs(polarity)
    if abs_polarity > 0.7:
        return "Very Strong"
    elif abs_polarity > 0.4:
        return "Strong"
    elif abs_polarity > 0.2:
        return "Moderate"
    elif abs_polarity > 0.05:
        return "Mild"
    else:
        return "Very Mild"

@bp.route('/analyze/sentiment', methods=['POST'])
@limiter.limit("200 per hour")
@optional_auth()
@swag_from({
    'tags': ['Sentiment Analysis'],
    'description': '''
    Analyze sentiment and tone of text without augmentation.
    
    **Tier Features:**
    - Free: Basic sentiment analysis
    - Basic+: Detailed analysis with emotion detection
    - Pro+: Advanced tone analysis and emotional intensity
    
    All tiers have access to sentiment analysis.
    ''',
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
                    'description': 'Text to analyze',
                    'example': 'I absolutely love this product! It works perfectly.'
                },
                'detailed': {
                    'type': 'boolean',
                    'default': False,
                    'description': 'Return detailed sentiment breakdown (Basic+ tier)'
                },
                'advanced': {
                    'type': 'boolean',
                    'default': False,
                    'description': 'Return advanced emotional analysis (Pro+ tier)'
                }
            }
        }
    }, {
        'name': 'X-API-Key',
        'in': 'header',
        'type': 'string',
        'required': False,
        'description': 'API key for tier-specific features (optional for free tier)'
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
                            'original': {'type': 'string'},
                            'sentiment': {
                                'type': 'object',
                                'properties': {
                                    'polarity': {'type': 'number'},
                                    'subjectivity': {'type': 'number'},
                                    'label': {'type': 'string'},
                                    'emoji': {'type': 'string'},
                                    'confidence': {'type': 'number'},
                                    'intensity': {'type': 'string'},
                                    'emotional_valence': {'type': 'string'}
                                }
                            },
                            'tone': {
                                'type': 'object',
                                'properties': {
                                    'primary': {'type': 'string'},
                                    'secondary': {'type': 'string'},
                                    'confidence': {'type': 'number'}
                                }
                            },
                            'metadata': {
                                'type': 'object',
                                'properties': {
                                    'word_count': {'type': 'integer'},
                                    'character_count': {'type': 'integer'},
                                    'analysis_type': {'type': 'string'},
                                    'user_tier': {'type': 'string'},
                                    'processing_time_ms': {'type': 'number'},
                                    'features_available': {'type': 'array', 'items': {'type': 'string'}}
                                }
                            },
                            'detailed_analysis': {
                                'type': 'object',
                                'properties': {
                                    'word_polarities': {
                                        'type': 'array',
                                        'items': {
                                            'type': 'object',
                                            'properties': {
                                                'word': {'type': 'string'},
                                                'polarity': {'type': 'number'},
                                                'contribution': {'type': 'number'}
                                            }
                                        }
                                    },
                                    'detected_emotions': {
                                        'type': 'array',
                                        'items': {
                                            'type': 'object',
                                            'properties': {
                                                'emotion': {'type': 'string'},
                                                'trigger_word': {'type': 'string'},
                                                'intensity': {'type': 'string'}
                                            }
                                        }
                                    },
                                    'sentence_analysis': {
                                        'type': 'array',
                                        'items': {
                                            'type': 'object',
                                            'properties': {
                                                'sentence': {'type': 'string'},
                                                'polarity': {'type': 'number'},
                                                'subjectivity': {'type': 'number'}
                                            }
                                        }
                                    }
                                }
                            },
                            'advanced_analysis': {
                                'type': 'object',
                                'properties': {
                                    'emotional_profile': {'type': 'object'},
                                    'psychological_indicators': {'type': 'array', 'items': {'type': 'string'}},
                                    'readability_score': {'type': 'number'},
                                    'complexity_metrics': {'type': 'object'}
                                }
                            },
                            'tier_limits': {
                                'type': 'object',
                                'properties': {
                                    'current_tier': {'type': 'string'},
                                    'daily_requests_remaining': {'type': 'integer'},
                                    'text_length_limit': {'type': 'integer'},
                                    'features_unlocked': {'type': 'array', 'items': {'type': 'string'}}
                                }
                            }
                        }
                    }
                }
            }
        },
        400: {'description': 'Bad Request'},
        402: {
            'description': 'Payment Required - advanced features require higher tier',
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
def analyze_sentiment_only():
    """
    Analyze sentiment and tone without text augmentation
    """
    start_time = time.time()
    data = request.get_json()
    
    if not data or 'text' not in data:
        return APIResponse.error(
            message="Missing 'text' field in request body",
            status_code=400
        )
    
    text = data.get('text', '').strip()
    detailed = data.get('detailed', False)
    advanced = data.get('advanced', False)
    
    if not text:
        return APIResponse.error(
            message="Text cannot be empty",
            status_code=400
        )
    
    # Get user info
    user = g.user
    user_tier = g.tier
    tier_limits = user.get_tier_limits()
    
    # Check text length against tier limits
    if len(text) > tier_limits['max_text_length']:
        return APIResponse.tier_limit_error(
            message=f'Text exceeds {user_tier} tier character limit of {tier_limits["max_text_length"]}.',
            current_tier=user_tier,
            suggested_tier='basic' if len(text) <= 2000 else 'pro',
            limit_details={
                'text_length': len(text),
                'allowed_length': tier_limits['max_text_length'],
                'feature': 'text_length'
            }
        )
    
    # Check if user can access detailed/advanced features
    if detailed and user_tier == 'free':
        return APIResponse.tier_limit_error(
            message='Detailed sentiment analysis requires Basic tier or higher.',
            current_tier=user_tier,
            suggested_tier='basic',
            required_tier='basic',
            limit_details={
                'feature': 'detailed_analysis',
                'allowed': False
            }
        )
    
    if advanced and user_tier in ['free', 'basic']:
        return APIResponse.tier_limit_error(
            message='Advanced emotional analysis requires Pro tier or higher.',
            current_tier=user_tier,
            suggested_tier='pro',
            required_tier='pro',
            limit_details={
                'feature': 'advanced_analysis',
                'allowed': False
            }
        )
    
    try:
        # Analyze sentiment
        sentiment_result = augmentor.analyze_sentiment(text)
        
        # Add intensity information
        sentiment_result['intensity'] = get_emotion_intensity(sentiment_result['polarity'])
        sentiment_result['emotional_valence'] = 'Positive' if sentiment_result['polarity'] > 0 else 'Negative' if sentiment_result['polarity'] < 0 else 'Neutral'
        
        # Detect tone with confidence
        tone = detect_tone(text)
        
        # Calculate tone confidence (simplified)
        tone_confidence = 0.7  # Base confidence
        if tone in ['Questioning', 'Excited/Emphatic', 'Very Excited/Emphatic']:
            tone_confidence = 0.9
        
        # Get word count
        word_count = len(text.split())
        
        # Prepare response data
        response_data = {
            'original': text,
            'sentiment': sentiment_result,
            'tone': {
                'primary': tone,
                'secondary': 'Neutral' if tone != 'Neutral/Informative' else 'Informative',
                'confidence': round(tone_confidence, 2)
            },
            'metadata': {
                'word_count': word_count,
                'character_count': len(text),
                'analysis_type': 'sentiment_only',
                'user_tier': user_tier,
                'processing_time_ms': 0,  # Will be updated later
                'features_available': ['basic_sentiment', 'tone_detection']
            }
        }
        
        # Add tier limits info
        today = datetime.utcnow().date().isoformat()
        daily_used = user.daily_requests.get(today, 0)
        daily_limit = tier_limits['daily_requests']
        
        response_data['tier_limits'] = {
            'current_tier': user_tier,
            'daily_requests_remaining': max(0, daily_limit - daily_used),
            'text_length_limit': tier_limits['max_text_length'],
            'features_unlocked': tier_limits['features'] if isinstance(tier_limits['features'], list) else ['all']
        }
        
        # Detailed analysis (Basic+ tier)
        if detailed and user_tier != 'free':
            blob = TextBlob(text)
            
            # Get individual word polarities with contribution scores
            word_polarities = []
            for sentence in blob.sentences:
                for word in sentence.words:
                    word_str = str(word)
                    word_blob = TextBlob(word_str)
                    word_polarity = word_blob.sentiment.polarity
                    
                    # Calculate contribution to overall sentiment
                    contribution = abs(word_polarity) / max(1, word_count)
                    
                    word_polarities.append({
                        'word': word_str,
                        'polarity': round(word_polarity, 3),
                        'contribution': round(contribution, 4)
                    })
            
            # Enhanced emotion detection
            emotion_categories = {
                'joy': ['happy', 'joy', 'delighted', 'ecstatic', 'pleased', 'content'],
                'anger': ['angry', 'furious', 'irate', 'annoyed', 'frustrated', 'outraged'],
                'sadness': ['sad', 'depressed', 'melancholy', 'unhappy', 'gloomy', 'heartbroken'],
                'fear': ['afraid', 'scared', 'terrified', 'fearful', 'anxious', 'worried'],
                'surprise': ['surprised', 'amazed', 'astonished', 'shocked', 'stunned'],
                'trust': ['trust', 'confident', 'certain', 'assured', 'reliable'],
                'disgust': ['disgusted', 'repulsed', 'revolted', 'sickened', 'nauseated'],
                'anticipation': ['excited', 'eager', 'hopeful', 'optimistic', 'expectant']
            }
            
            detected_emotions = []
            text_lower = text.lower()
            for emotion, words in emotion_categories.items():
                for word in words:
                    if word in text_lower:
                        # Calculate intensity based on modifiers
                        intensity = 'moderate'
                        if f'very {word}' in text_lower or f'extremely {word}' in text_lower:
                            intensity = 'high'
                        elif f'slightly {word}' in text_lower or f'a bit {word}' in text_lower:
                            intensity = 'low'
                        
                        detected_emotions.append({
                            'emotion': emotion.capitalize(),
                            'trigger_word': word,
                            'intensity': intensity.capitalize()
                        })
                        break
            
            # Sentence-level analysis
            sentence_analysis = []
            for i, sentence in enumerate(blob.sentences):
                sentence_str = str(sentence)
                sentence_blob = TextBlob(sentence_str)
                sentence_analysis.append({
                    'sentence': sentence_str,
                    'polarity': round(sentence_blob.sentiment.polarity, 3),
                    'subjectivity': round(sentence_blob.sentiment.subjectivity, 3),
                    'position': i + 1,
                    'word_count': len(sentence_str.split())
                })
            
            response_data['detailed_analysis'] = {
                'word_polarities': word_polarities[:50],  # Limit to top 50
                'detected_emotions': detected_emotions,
                'sentence_analysis': sentence_analysis,
                'overall_metrics': {
                    'avg_sentence_length': round(sum(len(str(s).split()) for s in blob.sentences) / max(1, len(list(blob.sentences))), 2),
                    'sentence_count': len(list(blob.sentences)),
                    'avg_word_length': round(sum(len(w) for w in text.split()) / word_count, 2),
                    'lexical_diversity': round(len(set(text.lower().split())) / word_count, 3) if word_count > 0 else 0
                }
            }
            
            response_data['metadata']['features_available'].extend(['detailed_analysis', 'emotion_detection'])
        
        # Advanced analysis (Pro+ tier)
        if advanced and user_tier in ['pro', 'enterprise']:
            blob = TextBlob(text)
            
            # Emotional profile
            emotional_profile = {
                'primary_emotion': sentiment_result['label'],
                'emotional_complexity': 'simple' if abs(sentiment_result['polarity']) > 0.7 else 'complex',
                'emotional_consistency': 'consistent' if sentiment_result['subjectivity'] > 0.7 else 'mixed',
                'expressiveness': 'high' if sentiment_result['subjectivity'] > 0.8 else 'medium' if sentiment_result['subjectivity'] > 0.5 else 'low'
            }
            
            # Psychological indicators (simplified)
            psychological_indicators = []
            if 'i ' in text_lower or ' me ' in text_lower or ' my ' in text_lower:
                psychological_indicators.append('Self-focused')
            if 'we ' in text_lower or ' us ' in text_lower or ' our ' in text_lower:
                psychological_indicators.append('Group-focused')
            if text.count('!') > 1:
                psychological_indicators.append('Expressive')
            if len(text.split()) > 50:
                psychological_indicators.append('Detailed thinker')
            
            # Readability score (simplified Flesch reading ease)
            sentences = list(blob.sentences)
            sentence_count = len(sentences)
            if sentence_count > 0 and word_count > 0:
                avg_sentence_length = word_count / sentence_count
                avg_syllables_per_word = sum(len(re.findall(r'[aeiouy]+', word.lower())) for word in text.split()) / word_count
                readability = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables_per_word
                readability_score = max(0, min(100, readability))
            else:
                readability_score = 0
            
            response_data['advanced_analysis'] = {
                'emotional_profile': emotional_profile,
                'psychological_indicators': psychological_indicators,
                'readability_score': round(readability_score, 2),
                'complexity_metrics': {
                    'flesch_kincaid_grade': round(0.39 * avg_sentence_length + 11.8 * avg_syllables_per_word - 15.59, 2) if 'avg_sentence_length' in locals() else 0,
                    'gunning_fog': round(0.4 * (avg_sentence_length + 100 * (sum(1 for word in text.split() if len(word) >= 3) / word_count)), 2) if 'avg_sentence_length' in locals() else 0,
                    'coleman_liau': round(5.88 * (sum(len(word) for word in text.split()) / word_count) - 29.6 * (sentence_count / word_count) - 15.8, 2) if word_count > 0 else 0
                }
            }
            
            response_data['metadata']['features_available'].extend(['advanced_analysis', 'psychological_indicators', 'readability_metrics'])
        
        # Calculate processing time
        processing_time = round((time.time() - start_time) * 1000, 2)
        response_data['metadata']['processing_time_ms'] = processing_time
        
        # Increment user request count
        user.increment_request_count()
        
        return APIResponse.success(
            data=response_data,
            message="Sentiment analysis completed successfully"
        )
        
    except Exception as e:
        return APIResponse.error(
            message="Failed to analyze sentiment",
            error=str(e),
            status_code=500
        )

@bp.route('/analyze/batch-sentiment', methods=['POST'])
@limiter.limit("100 per hour")
@require_auth(feature='batch')
@swag_from({
    'tags': ['Batch Processing', 'Sentiment Analysis'],
    'description': '''
    Analyze sentiment for multiple texts in batch.
    
    **Tier Limits:**
    - Basic: Up to 20 texts per batch
    - Pro: Up to 100 texts per batch
    - Enterprise: Up to 500 texts per batch
    
    Free tier does not include batch sentiment analysis.
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
                    'maxItems': 500,
                    'items': {
                        'type': 'string',
                        'description': 'Text to analyze'
                    }
                },
                'detailed': {
                    'type': 'boolean',
                    'default': False,
                    'description': 'Include detailed analysis for each text'
                }
            }
        }
    }, {
        'name': 'X-API-Key',
        'in': 'header',
        'type': 'string',
        'required': True,
        'description': 'API key (batch analysis requires authentication)'
    }],
    'responses': {
        200: {'description': 'Success'},
        400: {'description': 'Bad Request'},
        402: {'description': 'Payment Required - batch analysis not available for free tier'}
    }
})
def analyze_batch_sentiment():
    """
    Analyze sentiment for multiple texts with tier enforcement
    """
    start_time = time.time()
    data = request.get_json()
    
    if not data or 'texts' not in data:
        return APIResponse.error(
            message="Missing 'texts' array in request body",
            status_code=400
        )
    
    texts = data['texts']
    detailed = data.get('detailed', False)
    
    if not isinstance(texts, list):
        return APIResponse.error(
            message="'texts' must be an array",
            status_code=400
        )
    
    # Get user info
    user = g.user
    user_tier = g.tier
    
    # Check batch size against tier limits
    tier_limits = user.get_tier_limits()
    max_batch_size = 20 if user_tier == 'basic' else 100 if user_tier == 'pro' else 500
    
    if len(texts) > max_batch_size:
        return APIResponse.tier_limit_error(
            message=f'{user_tier.capitalize()} tier allows maximum {max_batch_size} texts per batch. You requested {len(texts)}.',
            current_tier=user_tier,
            suggested_tier='pro' if user_tier == 'basic' else 'enterprise',
            limit_details={
                'requested': len(texts),
                'allowed': max_batch_size,
                'feature': 'batch_size'
            }
        )
    
    if len(texts) < 1:
        return APIResponse.error(
            message="Must provide at least 1 text",
            status_code=400
        )
    
    # Check if detailed analysis is allowed for this tier
    if detailed and user_tier == 'basic':
        return APIResponse.tier_limit_error(
            message='Detailed batch analysis requires Pro tier or higher.',
            current_tier=user_tier,
            suggested_tier='pro',
            required_tier='pro',
            limit_details={
                'feature': 'detailed_batch_analysis',
                'allowed': False
            }
        )
    
    results = []
    processing_times = []
    
    # Process texts (could be parallelized for large batches)
    for i, text in enumerate(texts):
        if not isinstance(text, str):
            results.append({
                'index': i,
                'success': False,
                'error': 'Text must be a string',
                'original': str(text)[:100]  # Truncate for error display
            })
            continue
        
        text = text.strip()
        if not text:
            results.append({
                'index': i,
                'success': False,
                'error': 'Text cannot be empty',
                'original': ''
            })
            continue
        
        # Check text length
        if len(text) > tier_limits['max_text_length']:
            results.append({
                'index': i,
                'success': False,
                'error': f'Text exceeds {user_tier} tier character limit of {tier_limits["max_text_length"]}',
                'original': text[:100] + '...' if len(text) > 100 else text
            })
            continue
        
        try:
            item_start_time = time.time()
            
            # Analyze sentiment
            sentiment_result = augmentor.analyze_sentiment(text)
            tone = detect_tone(text)
            
            result = {
                'index': i,
                'success': True,
                'original': text[:200] + '...' if len(text) > 200 else text,
                'sentiment': sentiment_result,
                'tone': tone,
                'word_count': len(text.split()),
                'text_length': len(text)
            }
            
            # Add detailed analysis if requested and allowed
            if detailed and user_tier in ['pro', 'enterprise']:
                blob = TextBlob(text)
                sentence_count = len(list(blob.sentences))
                
                # Simple emotion detection for batch
                emotion_words = {
                    'positive': ['love', 'great', 'excellent', 'wonderful', 'happy', 'perfect'],
                    'negative': ['hate', 'terrible', 'awful', 'bad', 'worst', 'horrible']
                }
                
                detected_emotions = []
                text_lower = text.lower()
                for emotion, words in emotion_words.items():
                    for word in words:
                        if word in text_lower:
                            detected_emotions.append(emotion)
                            break
                
                result['detailed'] = {
                    'sentence_count': sentence_count,
                    'detected_emotions': detected_emotions,
                    'avg_word_length': round(sum(len(w) for w in text.split()) / len(text.split()), 2) if text.split() else 0
                }
            
            processing_times.append(time.time() - item_start_time)
            results.append(result)
            
        except Exception as e:
            results.append({
                'index': i,
                'success': False,
                'original': text[:100] + '...' if len(text) > 100 else text,
                'error': str(e),
                'error_type': type(e).__name__
            })
    
    # Calculate statistics
    successful = [r for r in results if r.get('success', False)]
    failed = len(results) - len(successful)
    
    if successful:
        # Sentiment distribution
        sentiments = [r['sentiment']['label'] for r in successful]
        sentiment_counts = {s: sentiments.count(s) for s in set(sentiments)}
        
        # Tone distribution
        tones = [r['tone'] for r in successful]
        tone_counts = {t: tones.count(t) for t in set(tones)}
        
        # Average metrics
        avg_polarity = sum(r['sentiment']['polarity'] for r in successful) / len(successful)
        avg_subjectivity = sum(r['sentiment']['subjectivity'] for r in successful) / len(successful)
        avg_word_count = sum(r['word_count'] for r in successful) / len(successful)
        
        summary = {
            'total_texts': len(texts),
            'successful_analyses': len(successful),
            'failed_analyses': failed,
            'success_rate': round(len(successful) / len(texts) * 100, 2),
            'sentiment_distribution': sentiment_counts,
            'tone_distribution': tone_counts,
            'dominant_sentiment': max(sentiment_counts.items(), key=lambda x: x[1])[0] if sentiment_counts else 'N/A',
            'dominant_tone': max(tone_counts.items(), key=lambda x: x[1])[0] if tone_counts else 'N/A',
            'average_metrics': {
                'polarity': round(avg_polarity, 3),
                'subjectivity': round(avg_subjectivity, 3),
                'word_count': round(avg_word_count, 2),
                'processing_time_ms': round(sum(processing_times) * 1000 / len(successful), 2) if processing_times else 0
            }
        }
    else:
        summary = {
            'total_texts': len(texts),
            'successful_analyses': 0,
            'failed_analyses': failed,
            'success_rate': 0
        }
    
    total_processing_time = round((time.time() - start_time) * 1000, 2)
    
    # Prepare response
    response_data = {
        'results': results,
        'summary': summary,
        'batch_metadata': {
            'total_texts': len(texts),
            'successful_count': len(successful),
            'failed_count': failed,
            'processing_time_ms': total_processing_time,
            'average_time_per_text': round(total_processing_time / len(texts), 2) if texts else 0,
            'user_tier': user_tier,
            'batch_size_limit': max_batch_size,
            'detailed_analysis_included': detailed and user_tier in ['pro', 'enterprise']
        }
    }
    
    # Add efficiency metrics for large batches
    if len(texts) > 10:
        estimated_serial_time = sum(processing_times) * 1000 if processing_times else 0
        efficiency_gain = round((1 - total_processing_time / estimated_serial_time) * 100, 2) if estimated_serial_time > 0 else 0
        response_data['batch_metadata']['efficiency'] = {
            'estimated_serial_time_ms': round(estimated_serial_time, 2),
            'parallel_efficiency_gain': efficiency_gain,
            'processing_speed': round(len(texts) / (total_processing_time / 1000), 2) if total_processing_time > 0 else 0  # texts per second
        }
    
    # Increment user request count (counts as one batch request)
    user.increment_request_count()
    
    return APIResponse.success(
        data=response_data,
        message=f"Batch sentiment analysis completed ({len(successful)} successful, {failed} failed)"
    )