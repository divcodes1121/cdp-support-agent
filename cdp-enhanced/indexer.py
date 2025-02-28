import os
import json
import pickle
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from pathlib import Path
import logging
from tqdm import tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Download NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

# Initialize stemmer and stopwords
stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    """Preprocess text for indexing."""
    # Lowercase the text
    text = text.lower()
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords and stem
    tokens = [stemmer.stem(token) for token in tokens if token.isalnum() and token not in stop_words]
    
    return ' '.join(tokens)

def load_documents():
    """Load all scraped documents."""
    data_dir = Path("data")
    documents = []
    
    # Iterate through platform directories
    for platform_dir in data_dir.iterdir():
        if platform_dir.is_dir():
            platform = platform_dir.name
            
            # Iterate through JSON files
            for json_file in tqdm(list(platform_dir.glob("*.json")), desc=f"Loading {platform} documents"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        doc = json.load(f)
                        
                    # Add platform info if not present
                    if 'platform' not in doc:
                        doc['platform'] = platform
                        
                    documents.append(doc)
                except Exception as e:
                    logger.error(f"Error loading {json_file}: {e}")
    
    logger.info(f"Loaded {len(documents)} documents")
    return documents

def create_index(documents):
    """Create TF-IDF index of documents."""
    # Extract text and metadata
    texts = []
    metadata = []
    
    for doc in documents:
        # Combine title and content
        title = doc.get('title', '')
        content = doc.get('content', '')
        text = f"{title}. {content}"
        
        # Preprocess text
        preprocessed_text = preprocess_text(text)
        
        texts.append(preprocessed_text)
        metadata.append({
            'url': doc.get('url', ''),
            'title': title,
            'platform': doc.get('platform', ''),
            'headings': doc.get('headings', [])
        })
    
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(texts)
    
    # Save index
    os.makedirs('data/index', exist_ok=True)
    with open('data/index/tfidf_vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)
    with open('data/index/tfidf_matrix.pkl', 'wb') as f:
        pickle.dump(tfidf_matrix, f)
    with open('data/index/documents.pkl', 'wb') as f:
        pickle.dump(documents, f)
    with open('data/index/metadata.pkl', 'wb') as f:
        pickle.dump(metadata, f)
    
    logger.info("Index created successfully")
    return vectorizer, tfidf_matrix, documents, metadata

def build_index():
    """Main function to build the index."""
    logger.info("Loading documents...")
    documents = load_documents()
    
    logger.info("Creating index...")
    vectorizer, matrix, docs, metadata = create_index(documents)
    
    logger.info("Indexing completed!")

if __name__ == "__main__":
    build_index()
