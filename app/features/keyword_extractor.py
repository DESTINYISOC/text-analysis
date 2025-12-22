"""
Keyword extraction feature
"""
from textblob import TextBlob
from collections import Counter
import string

class KeywordExtractor:
    """Premium feature: Keyword extraction"""
    
    def __init__(self):
        self.stop_words = set([
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 
            'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'can', 'may', 'might', 'must'
        ])
    
    def extract_keywords(self, text: str, top_n: int = 10) -> dict:
        """
        Extract keywords from text
        
        Args:
            text: Input text
            top_n: Number of keywords to extract
            
        Returns:
            Dictionary with keywords and scores
        """
        if not text or len(text.strip()) == 0:
            return {
                'keywords': [],
                'total_keywords_found': 0,
                'text_complexity': 0,
                'error': 'Text cannot be empty'
            }
        
        # Clean text
        text_lower = text.lower()
        
        # Remove punctuation
        translator = str.maketrans('', '', string.punctuation)
        text_clean = text_lower.translate(translator)
        
        # Get words
        words = text_clean.split()
        
        # Remove stop words and short words
        filtered_words = [
            word for word in words 
            if word not in self.stop_words and len(word) > 2
        ]
        
        # Calculate frequencies
        word_freq = Counter(filtered_words)
        
        # Get top keywords
        top_keywords = word_freq.most_common(top_n)
        
        # Calculate metrics
        total_words = len(filtered_words)
        keywords_with_metrics = []
        
        for word, freq in top_keywords:
            tf = round(freq / total_words, 4) if total_words > 0 else 0
            importance = round(tf * 100, 2)
            
            keywords_with_metrics.append({
                'keyword': word,
                'frequency': freq,
                'tf': tf,
                'importance_score': importance,
                'category': self._categorize_keyword(word)
            })
        
        # Calculate text complexity
        unique_words = len(word_freq)
        total_filtered_words = len(filtered_words)
        text_complexity = round((unique_words / total_filtered_words * 100), 2) if total_filtered_words > 0 else 0
        
        return {
            'keywords': keywords_with_metrics,
            'total_keywords_found': unique_words,
            'text_complexity': text_complexity,
            'total_words_analyzed': total_filtered_words
        }
    
    def _categorize_keyword(self, keyword: str) -> str:
        """Simple keyword categorization"""
        # Basic categorization - you can expand this
        tech_words = ['api', 'software', 'code', 'program', 'system', 'data', 
                     'algorithm', 'network', 'database', 'server', 'cloud']
        business_words = ['business', 'market', 'customer', 'product', 'service', 
                         'sales', 'revenue', 'profit', 'growth', 'strategy']
        emotion_words = ['happy', 'sad', 'angry', 'excited', 'frustrated', 'love',
                        'hate', 'amazing', 'terrible', 'wonderful', 'disappointing']
        
        if keyword in tech_words:
            return 'technology'
        elif keyword in business_words:
            return 'business'
        elif keyword in emotion_words:
            return 'emotion'
        elif keyword.endswith(('ing', 'ed')):  # Basic verb detection
            return 'action'
        elif keyword.endswith(('ly')):  # Adverb detection
            return 'modifier'
        else:
            return 'general'

# Create a singleton instance
keyword_extractor = KeywordExtractor()