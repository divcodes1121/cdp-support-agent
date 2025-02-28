import pickle
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize stemmer and stopwords
stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))

# Regular expressions for query classification
how_to_patterns = [
    r'how (to|do|can|should)',
    r'steps (to|for)',
    r'guide (to|for)',
    r'tutorial',
    r'instructions',
    r'process (of|for)'
]

comparison_patterns = [
    r'compare',
    r'difference between',
    r'vs',
    r'versus',
    r'which is better',
    r'pros and cons'
]

class QueryProcessor:
    """Processes user queries and retrieves relevant information."""
    
    def __init__(self):
        """Initialize the query processor."""
        try:
            # Load index data
            with open('data/index/tfidf_vectorizer.pkl', 'rb') as f:
                self.vectorizer = pickle.load(f)
            with open('data/index/tfidf_matrix.pkl', 'rb') as f:
                self.tfidf_matrix = pickle.load(f)
            with open('data/index/documents.pkl', 'rb') as f:
                self.documents = pickle.load(f)
            with open('data/index/metadata.pkl', 'rb') as f:
                self.metadata = pickle.load(f)
                
            logger.info("Index loaded successfully")
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            # Initialize empty data structures as fallback
            self.vectorizer = None
            self.tfidf_matrix = None
            self.documents = []
            self.metadata = []
    
    def preprocess_query(self, query):
        """Preprocess a query for retrieval."""
        # Lowercase the query
        query = query.lower()
        
        # Tokenize
        tokens = word_tokenize(query)
        
        # Remove stopwords and stem
        tokens = [stemmer.stem(token) for token in tokens if token.isalnum() and token not in stop_words]
        
        return ' '.join(tokens)
    
    def classify_query(self, query):
        """Classify the type of query."""
        query = query.lower()
        
        # Check for how-to questions
        for pattern in how_to_patterns:
            if re.search(pattern, query):
                return "how-to"
        
        # Check for comparison questions
        for pattern in comparison_patterns:
            if re.search(pattern, query):
                return "comparison"
        
        # Default to general query
        return "general"
    
    def extract_platforms(self, query):
        """Extract mentioned CDP platforms from query."""
        query = query.lower()
        platforms = []
        
        platform_names = ["segment", "mparticle", "lytics", "zeotap"]
        for platform in platform_names:
            if platform in query:
                platforms.append(platform)
        
        return platforms
    
    def retrieve_documents(self, query, top_k=5, platforms=None):
        """Retrieve relevant documents for a query."""
        # Check if index is loaded
        if not self.vectorizer or not self.tfidf_matrix:
            return []
        
        # Preprocess query
        processed_query = self.preprocess_query(query)
        
        # Transform query to TF-IDF space
        query_vector = self.vectorizer.transform([processed_query])
        
        # Calculate similarity with all documents
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Get indices with similarities
        indices_with_scores = [(i, similarities[i]) for i in range(len(similarities))]
        
        # Filter by platforms if specified
        if platforms:
            # Filter by platforms
            platform_indices = []
            for i, meta in enumerate(self.metadata):
                if meta.get('platform') in platforms:
                    platform_indices.append((i, similarities[i]))
            indices_with_scores = platform_indices
        
        # Sort by score (descending) and take top_k
        top_indices = sorted(indices_with_scores, key=lambda x: x[1], reverse=True)[:top_k]
        
        # Retrieve top documents
        results = []
        for idx, score in top_indices:
            if float(score) > 0.1:  # Minimum similarity threshold
                results.append({
                    'document': self.documents[idx],
                    'metadata': self.metadata[idx],
                    'score': float(score)
                })
        
        return results
    
    def process_query(self, query):
        """Process a user query and return relevant information."""
        # Check if query is empty
        if not query.strip():
            return {
                'type': 'error',
                'message': 'Please provide a valid question.',
                'results': []
            }
        
        # Classify query
        query_type = self.classify_query(query)
        
        # Extract mentioned platforms
        platforms = self.extract_platforms(query)
        
        # Process based on query type
        if query_type == "comparison":
            return self.process_comparison_query(query, platforms)
        else:
            return self.process_regular_query(query, query_type, platforms)
    
    def process_regular_query(self, query, query_type, platforms):
        """Process a regular (non-comparison) query."""
        # Check if query is relevant to CDPs
        if not platforms and not any(word in query.lower() for word in ["cdp", "customer data platform", "data"]):
            return {
                'type': 'irrelevant',
                'message': "I'm sorry, but your question doesn't seem to be related to the CDP platforms I support. I can answer questions about Segment, mParticle, Lytics, and Zeotap.",
                'results': []
            }
        
        # Retrieve relevant documents
        results = self.retrieve_documents(query, platforms=platforms)
        
        # Check if any results were found
        if not results:
            return {
                'type': 'no_results',
                'message': "I couldn't find information related to your question. Could you try rephrasing or asking a different question about one of the CDP platforms?",
                'results': []
            }
        
        return {
            'type': query_type,
            'results': results,
            'platforms': platforms
        }
    
    def process_comparison_query(self, query, platforms):
        """Process a comparison query."""
        # If fewer than 2 platforms mentioned, use default comparison
        if len(platforms) < 2:
            # Get all platforms if none specified
            if not platforms:
                platforms = ["segment", "mparticle", "lytics", "zeotap"]
            
            # Get at least 2 platforms for comparison
            if len(platforms) == 1:
                other_platforms = [p for p in ["segment", "mparticle", "lytics", "zeotap"] if p != platforms[0]]
                platforms.append(other_platforms[0])
        
        # Limit to at most 2 platforms for focused comparison
        platforms = platforms[:2]
        
        # Get results for each platform
        platform_results = {}
        for platform in platforms:
            results = self.retrieve_documents(query, top_k=3, platforms=[platform])
            platform_results[platform] = results
        
        # Check if any results were found
        if all(not results for results in platform_results.values()):
            return {
                'type': 'no_results',
                'message': "I couldn't find enough information to compare the CDP platforms based on your question. Could you try asking a more specific comparison question?",
                'results': []
            }
        
        return {
            'type': 'comparison',
            'results': platform_results,
            'platforms': platforms
        }
