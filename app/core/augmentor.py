"""
Core text augmentation logic
"""
import re
import random
from collections import Counter
from typing import List, Dict, Tuple, Optional
from textblob import TextBlob
import nltk
from nltk.corpus import wordnet, brown  # Brown corpus for word frequency

class TextAugmentor:
    """
    Main class for text augmentation with sentiment analysis and synonym replacement
    """
    
    # POS tags to target for replacement (from safest to least safe)
    REPLACEABLE_TAGS = {
        'JJ', 'JJR', 'JJS',      # Adjectives
        'RB', 'RBR', 'RBS',      # Adverbs
        'NN', 'NNS',             # Common nouns
        'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'  # Verbs
    }
    
    # Words to never replace (critical for sentence meaning)
    BLACKLIST_WORDS = {
        # Articles
        'the', 'a', 'an',
        # Core verbs
        'be', 'is', 'are', 'was', 'were', 'am', 'been',
        'have', 'has', 'had', 'do', 'does', 'did',
        # Pronouns
        'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'me', 'him', 'her', 'us', 'them',
        # Conjunctions
        'and', 'or', 'but', 'nor', 'so', 'yet', 'for',
        'although', 'because', 'since', 'unless', 'while',
        # Prepositions
        'in', 'on', 'at', 'by', 'with', 'about', 'against',
        'between', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'from', 'up', 'down',
        'to', 'of', 'for'
    }
    
    def __init__(self):
        """Initialize the augmentor"""
        # Ensure NLTK data is downloaded
        self._ensure_nltk_data()
        
    def _ensure_nltk_data(self):
        """Ensure required NLTK data is available"""
        try:
            wordnet.ensure_loaded()
        except LookupError:
            nltk.download('wordnet')
            nltk.download('averaged_perceptron_tagger')
    
    @staticmethod
    def get_wordnet_pos(treebank_tag: str) -> Optional[str]:
        """
        Convert Treebank POS tags to WordNet POS tags
        
        Args:
            treebank_tag: POS tag from TextBlob
            
        Returns:
            WordNet POS tag or None if not convertible
        """
        if treebank_tag.startswith('J'):
            return wordnet.ADJ
        elif treebank_tag.startswith('V'):
            return wordnet.VERB
        elif treebank_tag.startswith('N'):
            return wordnet.NOUN
        elif treebank_tag.startswith('R'):
            return wordnet.ADV
        return None
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of text
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with sentiment analysis results
        """
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Enhanced sentiment classification
        if polarity > 0.75:
            label = "Very Positive"
            emoji = "😄"
        elif polarity > 0.3:
            label = "Positive"
            emoji = "🙂"
        elif polarity > 0.1:
            label = "Slightly Positive"
            emoji = "😊"
        elif polarity < -0.75:
            label = "Very Negative"
            emoji = "😠"
        elif polarity < -0.3:
            label = "Negative"
            emoji = "😞"
        elif polarity < -0.1:
            label = "Slightly Negative"
            emoji = "😐"
        else:
            label = "Neutral"
            emoji = "😐"
        
        return {
            "polarity": round(polarity, 4),
            "subjectivity": round(subjectivity, 4),
            "label": label,
            "emoji": emoji,
            "confidence": round(abs(polarity), 4)  # Higher abs(polarity) = more confident
        }
    
    def get_synonyms(self, word: str, pos_tag: str, max_synonyms: int = 5) -> List[str]:
        """
        Get relevant synonyms for a word
        
        Args:
            word: The word to find synonyms for
            pos_tag: Treebank POS tag
            max_synonyms: Maximum number of synonyms to return
            
        Returns:
            List of synonyms
        """
        wordnet_pos = self.get_wordnet_pos(pos_tag)
        if not wordnet_pos:
            return []
        
        synonyms = set()
        
        try:
            # Get synsets for the word with correct POS
            synsets = wordnet.synsets(word, pos=wordnet_pos)
            
            # Collect synonyms from synsets (prioritizing common ones)
            for synset in synsets[:3]:  # Limit to 3 most common meanings
                for lemma in synset.lemmas():
                    synonym = lemma.name().replace('_', ' ').lower()
                    
                    # Filter criteria
                    if (synonym != word.lower() and
                        synonym not in self.BLACKLIST_WORDS and
                        len(synonym.split()) == 1 and  # Single word only
                        synonym.isalpha()):  # Letters only
                        
                        synonyms.add(synonym)
                        
                        if len(synonyms) >= max_synonyms:
                            break
                
                if len(synonyms) >= max_synonyms:
                    break
        except Exception as e:
            print(f"Error getting synonyms for '{word}': {e}")
        
        return list(synonyms)[:max_synonyms]
    
    def find_replaceable_words(self, text: str) -> List[Dict]:
        """
        Find all replaceable words in text
        
        Args:
            text: Input text
            
        Returns:
            List of dictionaries with word info
        """
        blob = TextBlob(text)
        words = blob.words
        tags = blob.tags
        
        replaceable_words = []
        
        for i, (word_obj, tag_tuple) in enumerate(zip(words, tags)):
            word = str(word_obj)
            tag = tag_tuple[1]
            
            # Skip if word is in blacklist
            if word.lower() in self.BLACKLIST_WORDS:
                continue
            
            # Check if POS tag is replaceable
            if tag in self.REPLACEABLE_TAGS:
                wordnet_pos = self.get_wordnet_pos(tag)
                if wordnet_pos:
                    synonyms = self.get_synonyms(word, tag)
                    if synonyms:  # Only include if synonyms exist
                        replaceable_words.append({
                            'index': i,
                            'original': word,
                            'pos_tag': tag,
                            'synonyms': synonyms,
                            'is_capitalized': word[0].isupper() if word else False
                        })
        
        return replaceable_words
    
    def augment_text(self, text: str, augmentation_count: int = 3) -> List[str]:
        """
        Generate augmented versions of text
        
        Args:
            text: Input text
            augmentation_count: Number of augmentations to generate
            
        Returns:
            List of augmented sentences
        """
        if augmentation_count <= 0:
            return []
        
        replaceable_words = self.find_replaceable_words(text)
        if not replaceable_words:
            return [text]  # Return original if no replaceable words
        
        # Limit augmentations to available words
        max_augmentations = min(augmentation_count, len(replaceable_words))
        augmentations = []
        
        # Create base word list
        blob = TextBlob(text)
        base_words = [str(w) for w in blob.words]
        
        # Track which words we've already replaced to avoid duplicates
        replaced_indices = set()
        
        for _ in range(max_augmentations):
            # Filter words that haven't been replaced yet
            available_words = [w for w in replaceable_words if w['index'] not in replaced_indices]
            
            if not available_words:
                break
            
            # Choose a random word to replace
            word_info = random.choice(available_words)
            idx = word_info['index']
            
            # Choose a random synonym
            if word_info['synonyms']:
                synonym = random.choice(word_info['synonyms'])
                
                # Preserve capitalization
                if word_info['is_capitalized']:
                    synonym = synonym.capitalize()
                
                # Create new word list
                new_words = base_words.copy()
                new_words[idx] = synonym
                
                # Reconstruct sentence (simplified - better reconstruction needed)
                # TODO: Implement better sentence reconstruction with punctuation
                augmented = ' '.join(new_words)
                augmentations.append(augmented)
                
                # Mark this index as used
                replaced_indices.add(idx)
        
        return augmentations
    
    def enrich_text(self, text: str, augmentation_count: int = 3) -> Dict:
        """
        Complete text enrichment pipeline
        
        Args:
            text: Input text
            augmentation_count: Number of augmentations to generate
            
        Returns:
            Complete enrichment results
        """
        sentiment = self.analyze_sentiment(text)
        augmentations = self.augment_text(text, augmentation_count)
        replaceable_words = self.find_replaceable_words(text)
        
        return {
            'sentiment': sentiment,
            'augmentations': augmentations,
            'replaceable_words_count': len(replaceable_words),
            'word_count': len(text.split()),
            'success': True
        }


class EnhancedTextAugmentor(TextAugmentor):
    """
    Enhanced augmentor with grammatical coherence and common word filtering
    """
    
    def __init__(self):
        super().__init__()
        # Load word frequency data
        self.word_frequencies = self._load_word_frequencies()
        # Common word threshold (top 50% most frequent words)
        self.common_word_threshold = 0.5
    
    def _load_word_frequencies(self) -> Dict[str, int]:
        """
        Load word frequency data from Brown corpus
        Returns dictionary of word -> frequency rank
        """
        try:
            nltk.download('brown', quiet=True)
            # Get frequency distribution
            words = brown.words()
            freq_dist = nltk.FreqDist(w.lower() for w in words)
            
            # Convert to rank dictionary
            sorted_words = sorted(freq_dist.items(), key=lambda x: x[1], reverse=True)
            word_ranks = {word: rank for rank, (word, _) in enumerate(sorted_words, 1)}
            
            return word_ranks
        except:
            # Fallback to simple frequency list
            return {}
    
    def is_common_word(self, word: str) -> bool:
        """
        Check if a word is common based on frequency
        """
        if not self.word_frequencies:
            return True  # If no frequency data, assume common
        
        rank = self.word_frequencies.get(word.lower(), float('inf'))
        total_words = len(self.word_frequencies)
        
        # Consider word common if it's in top 50%
        return rank <= total_words * self.common_word_threshold
    
    def get_grammatically_matching_synonyms(self, word: str, pos_tag: str, 
                                           max_synonyms: int = 5) -> List[str]:
        """
        Get synonyms that match grammatical role and are common words
        """
        # Get all possible synonyms
        all_synonyms = self.get_synonyms(word, pos_tag, max_synonyms * 3)
        
        # Filter by grammatical compatibility
        compatible_synonyms = []
        for synonym in all_synonyms:
            # Check if synonym can serve same grammatical role
            if self._is_grammatically_compatible(word, synonym, pos_tag):
                compatible_synonyms.append(synonym)
        
        # Filter by word commonality
        common_synonyms = [s for s in compatible_synonyms if self.is_common_word(s)]
        
        # If no common synonyms, fall back to compatible ones
        if not common_synonyms and compatible_synonyms:
            return compatible_synonyms[:max_synonyms]
        
        # Return most common synonyms first
        common_synonyms.sort(key=lambda x: self.word_frequencies.get(x.lower(), float('inf')))
        return common_synonyms[:max_synonyms]
    
    def _is_grammatically_compatible(self, original: str, synonym: str, 
                                    pos_tag: str) -> bool:
        """
        Check if synonym can replace original in same grammatical role
        """
        # Basic compatibility checks
        if pos_tag.startswith('JJ'):  # Adjective
            # Check if synonym can be used as adjective
            return self._can_be_adjective(synonym)
        
        elif pos_tag.startswith('VB'):  # Verb
            # Check if synonym can be used as verb
            return self._can_be_verb(synonym)
        
        elif pos_tag.startswith('NN'):  # Noun
            # Check if synonym can be used as noun
            return self._can_be_noun(synonym)
        
        elif pos_tag.startswith('RB'):  # Adverb
            # Check if synonym can be used as adverb
            return self._can_be_adverb(synonym)
        
        return True  # Default to true if we can't determine
    
    def _can_be_adjective(self, word: str) -> bool:
        """Check if word can function as adjective"""
        synsets = wordnet.synsets(word, pos=wordnet.ADJ)
        return len(synsets) > 0
    
    def _can_be_verb(self, word: str) -> bool:
        """Check if word can function as verb"""
        synsets = wordnet.synsets(word, pos=wordnet.VERB)
        return len(synsets) > 0
    
    def _can_be_noun(self, word: str) -> bool:
        """Check if word can function as noun"""
        synsets = wordnet.synsets(word, pos=wordnet.NOUN)
        return len(synsets) > 0
    
    def _can_be_adverb(self, word: str) -> bool:
        """Check if word can function as adverb"""
        synsets = wordnet.synsets(word, pos=wordnet.ADV)
        return len(synsets) > 0
    
    def augment_text_with_grammar(self, text: str, augmentation_count: int = 3) -> List[str]:
        """
        Enhanced augmentation with grammatical coherence
        """
        # Parse sentence preserving punctuation
        tokens = re.findall(r'\w+|[^\w\s]', text)
        
        # Get word indices and POS tags
        blob = TextBlob(text)
        words = blob.words
        tags = blob.tags
        
        replaceable_words = []
        for i, (word_obj, tag_tuple) in enumerate(zip(words, tags)):
            word = str(word_obj)
            tag = tag_tuple[1]
            
            if tag in self.REPLACEABLE_TAGS and word.lower() not in self.BLACKLIST_WORDS:
                synonyms = self.get_grammatically_matching_synonyms(word, tag, 3)
                if synonyms:
                    replaceable_words.append({
                        'index': i,
                        'original': word,
                        'tag': tag,
                        'synonyms': synonyms,
                        'is_capitalized': word[0].isupper()
                    })
        
        if not replaceable_words:
            return [text]
        
        augmentations = []
        base_words = [str(w) for w in words]
        
        for _ in range(min(augmentation_count, len(replaceable_words))):
            word_info = random.choice(replaceable_words)
            idx = word_info['index']
            
            if word_info['synonyms']:
                synonym = random.choice(word_info['synonyms'])
                
                # Preserve capitalization
                if word_info['is_capitalized']:
                    synonym = synonym.capitalize()
                
                # Create new sentence with proper spacing
                new_words = base_words.copy()
                new_words[idx] = synonym
                
                # Reconstruct with original punctuation pattern
                augmented = self._reconstruct_sentence(new_words, tokens)
                augmentations.append(augmented)
        
        return augmentations
    
    def _reconstruct_sentence(self, new_words: List[str], 
                             original_tokens: List[str]) -> str:
        """
        Reconstruct sentence preserving original punctuation
        """
        result = []
        word_index = 0
        
        for token in original_tokens:
            if token.isalpha():
                if word_index < len(new_words):
                    result.append(new_words[word_index])
                    word_index += 1
            else:
                result.append(token)
        
        # Handle spaces
        sentence = ''
        for i, token in enumerate(result):
            if i > 0 and token.isalnum() and result[i-1].isalnum():
                sentence += ' ' + token
            else:
                sentence += token
        
        return sentence.strip()

# Replace the existing augmentor with enhanced version
augmentor = EnhancedTextAugmentor()