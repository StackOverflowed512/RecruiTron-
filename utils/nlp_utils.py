import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download all required NLTK resources
def download_nltk_resources():
    resources = [
        'punkt',
        'stopwords',
        'averaged_perceptron_tagger',
        'maxent_ne_chunker',
        'words'
    ]
    for resource in resources:
        try:
            nltk.data.find(f'tokenizers/{resource}')
        except LookupError:
            print(f'Downloading {resource}...')
            nltk.download(resource, quiet=True)

# Download resources when module is imported
download_nltk_resources()

def clean_text(text):
    """Clean and preprocess text"""
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    
    # Remove mentions and hashtags
    text = re.sub(r'@\w+|#\w+', '', text)
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Remove numbers
    text = re.sub(r'\d+', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_keywords(text, n=10):
    """Extract top n keywords from text"""
    if not text:
        return []
    
    # Clean text first
    text = clean_text(text)
    
    # Tokenize and remove stopwords
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text)
    filtered_words = [word for word in word_tokens if word not in stop_words and len(word) > 2]
    
    # Count word frequencies
    word_freq = nltk.FreqDist(filtered_words)
    
    # Get most common words
    keywords = [word for word, _ in word_freq.most_common(n)]
    
    return keywords