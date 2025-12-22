"""
Text summarization feature
"""
from textblob import TextBlob
from collections import Counter
import heapq

class TextSummarizer:
    """Premium feature: Text summarization"""
    
    def __init__(self):
        self.stop_words = set(['the', 'a', 'an', 'in', 'on', 'at', 'and', 'or', 
                              'but', 'is', 'are', 'was', 'were', 'to', 'of', 'for'])
    
    def summarize(self, text: str, num_sentences: int = 3) -> dict:
        """
        Generate a summary of the text
        
        Args:
            text: Input text
            num_sentences: Number of sentences in summary
            
        Returns:
            Dictionary with summary and metrics
        """
        if not text or len(text.strip()) == 0:
            return {
                'summary': '',
                'reduction_percent': 0,
                'original_sentences': 0,
                'summary_sentences': 0,
                'error': 'Text cannot be empty'
            }
        
        # Split into sentences
        blob = TextBlob(text)
        sentences = [str(s).strip() for s in blob.sentences]
        
        if len(sentences) <= num_sentences:
            return {
                'summary': text,
                'reduction_percent': 0,
                'original_sentences': len(sentences),
                'summary_sentences': len(sentences),
                'note': 'Text already shorter than requested summary length'
            }
        
        # Calculate word frequencies (excluding stop words)
        words = [word.lower() for word in blob.words 
                if word.lower() not in self.stop_words and len(word) > 2]
        word_freq = Counter(words)
        
        # Score sentences based on word frequency
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            score = 0
            sentence_words = TextBlob(sentence).words
            sentence_word_count = len(sentence_words)
            
            for word in sentence_words:
                word_lower = word.lower()
                if word_lower in word_freq:
                    score += word_freq[word_lower]
            
            if sentence_word_count > 0:
                score = score / sentence_word_count  # Normalize by sentence length
            
            sentence_scores[i] = score
        
        # Get top sentences
        top_sentence_indices = heapq.nlargest(
            num_sentences, 
            sentence_scores, 
            key=sentence_scores.get
        )
        top_sentence_indices.sort()  # Maintain original order
        
        # Generate summary
        summary = ' '.join(sentences[i] for i in top_sentence_indices)
        
        return {
            'summary': summary,
            'reduction_percent': round((1 - len(summary.split()) / len(text.split())) * 100, 2),
            'original_sentences': len(sentences),
            'summary_sentences': num_sentences,
            'original_length': len(text),
            'summary_length': len(summary),
            'original_word_count': len(text.split()),
            'summary_word_count': len(summary.split())
        }

# Create a singleton instance
summarizer = TextSummarizer()