import nltk
import re
from nltk.sentiment import SentimentIntensityAnalyzer
import string
from collections import Counter

class SentimentAnalyzer:
    def __init__(self, gemini_model=None):
        self.model = gemini_model
        # Download NLTK resources if needed
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon', quiet=True)
        
        try:
            nltk.data.find('punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
            
        try:
            nltk.data.find('stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
        
        # Initialize VADER sentiment analyzer
        self.sia = SentimentIntensityAnalyzer()
        self.stopwords = set(nltk.corpus.stopwords.words('english'))
        
        # Common filler words beyond basic stopwords
        self.filler_words = set([
            'um', 'uh', 'er', 'ah', 'like', 'actually', 'basically', 
            'literally', 'you know', 'i mean', 'sort of', 'kind of',
            'so', 'just', 'well', 'anyway', 'right'
        ])
        
        # Confidence indicators (positive and negative)
        self.confidence_markers = {
            'positive': [
                'confident', 'certainly', 'definitely', 'absolutely', 'surely',
                'undoubtedly', 'clearly', 'obviously', 'precisely', 'exactly',
                'I know', 'I am sure', 'without doubt', 'I believe',
                'I am confident', 'I am certain'
            ],
            'negative': [
                'maybe', 'perhaps', 'possibly', 'probably', 'somewhat',
                'I think', 'I guess', 'kind of', 'sort of', 'might',
                'I suppose', 'I assume', 'not sure', 'uncertain', 'unsure',
                'hopefully', 'seems like', 'in my opinion', 'if I recall'
            ]
        }
        
    def analyze_text(self, text):
        """Analyze sentiment, confidence, clarity, and relevance of text"""
        if not text:
            return {
                'sentiment': {'positive': 0, 'negative': 0, 'neutral': 1, 'compound': 0},
                'confidence': 0,
                'clarity': 0,
                'filler_ratio': 0,
                'avg_sentence_length': 0,
                'vocabulary_richness': 0
            }
        
        # Get sentiment scores
        sentiment = self.sia.polarity_scores(text)
        
        # Analyze confidence markers
        confidence_score = self.analyze_confidence(text)
        
        # Analyze clarity
        clarity_metrics = self.analyze_clarity(text)
        
        # Combine all metrics
        result = {
            'sentiment': {
                'positive': sentiment['pos'],
                'negative': sentiment['neg'],
                'neutral': sentiment['neu'],
                'compound': sentiment['compound']
            },
            'confidence': confidence_score,
            **clarity_metrics
        }
        
        return result
    
    def analyze_confidence(self, text):
        """Analyze confidence level in text based on markers"""
        text_lower = text.lower()
        
        # Count positive and negative confidence markers
        positive_count = sum(1 for marker in self.confidence_markers['positive'] 
                            if re.search(r'\b' + re.escape(marker.lower()) + r'\b', text_lower))
        
        negative_count = sum(1 for marker in self.confidence_markers['negative']
                            if re.search(r'\b' + re.escape(marker.lower()) + r'\b', text_lower))
        
        # Word count for normalization
        words = text.split()
        word_count = len(words)
        
        if word_count == 0:
            return 50  # Neutral score for empty text
        
        # Calculate confidence score (0-100)
        # Base score of 50 (neutral)
        # Each positive marker adds points, each negative marker subtracts points
        # Normalize by text length to avoid favoring longer responses
        base_score = 50
        positive_impact = min(40, (positive_count / (word_count / 100)) * 10)
        negative_impact = min(40, (negative_count / (word_count / 100)) * 10)
        
        confidence_score = base_score + positive_impact - negative_impact
        
        # Ensure score stays within 0-100 range
        return max(0, min(100, confidence_score))
    
    def analyze_clarity(self, text):
        """Analyze clarity of text including filler words, sentence length, vocabulary richness"""
        # Tokenize text
        sentences = nltk.sent_tokenize(text)
        words = nltk.word_tokenize(text.lower())
        
        # Filter out punctuation
        words = [word for word in words if word not in string.punctuation]
        
        # Count filler words
        filler_count = sum(1 for word in words 
                          if word in self.filler_words or 
                          any(filler in text.lower() for filler in self.filler_words))
        
        word_count = len(words)
        filler_ratio = filler_count / word_count if word_count > 0 else 0
        
        # Calculate average sentence length
        sentence_lengths = [len(nltk.word_tokenize(s)) for s in sentences]
        avg_sentence_length = sum(sentence_lengths) / len(sentences) if sentences else 0
        
        # Calculate vocabulary richness (type-token ratio)
        # Ignore stopwords for a more meaningful measure
        content_words = [w for w in words if w not in self.stopwords]
        unique_words = set(content_words)
        vocabulary_richness = len(unique_words) / len(content_words) if content_words else 0
        
        # Normalize metrics to 0-100 scale
        # Ideal filler ratio is close to 0
        normalized_filler = max(0, 100 - (filler_ratio * 100 * 5))  # Penalize heavily for fillers
        
        # Ideal sentence length is 15-20 words
        if avg_sentence_length < 5:
            normalized_sentence_length = avg_sentence_length * 10  # Too short
        elif avg_sentence_length > 30:
            normalized_sentence_length = max(0, 100 - (avg_sentence_length - 30) * 3)  # Too long
        else:
            # Sweet spot around 15-25 words
            normalized_sentence_length = 100 - abs(20 - avg_sentence_length) * 2
        
        # Vocabulary richness ideally around 0.6-0.8
        if vocabulary_richness < 0.3:
            normalized_vocabulary = vocabulary_richness * 100 * 2  # Limited vocabulary
        elif vocabulary_richness > 0.9:
            normalized_vocabulary = 100 - (vocabulary_richness - 0.9) * 100  # Too complex/varied
        else:
            normalized_vocabulary = 60 + vocabulary_richness * 50  # Good range
        
        # Combined clarity score
        clarity_score = (normalized_filler + normalized_sentence_length + normalized_vocabulary) / 3
        
        return {
            'clarity': max(0, min(100, clarity_score)),
            'filler_ratio': filler_ratio,
            'avg_sentence_length': avg_sentence_length,
            'vocabulary_richness': vocabulary_richness
        }