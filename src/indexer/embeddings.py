"""
Text embedding utilities for the CDP documentation.
"""

import logging
from typing import List, Dict, Union

from langchain.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer

from src.config import EMBEDDING_MODEL

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DocumentEmbedder:
    """
    Embedder for document content.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        Initialize the document embedder.

        Args:
            model_name: Name of the embedding model to use.
        """
        logger.info(f"Initializing embedder with model: {model_name}")
        self.model_name = model_name
        
        # Initialize the embedding model
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
            self._model = SentenceTransformer(model_name)
            logger.info("Embedding model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing embedding model: {e}")
            raise

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embeddings for a text.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector.
        """
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        try:
            return self.embeddings.embed_documents(texts)
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return []

    def embed_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Generate embeddings for a list of document chunks.

        Args:
            documents: List of document chunks.

        Returns:
            List of document chunks with embeddings.
        """
        # Extract content from documents
        contents = [doc["content"] for doc in documents]
        
        # Generate embeddings for contents
        embeddings = self.embed_batch(contents)
        
        # Add embeddings to documents
        for i, doc in enumerate(documents):
            doc["embedding"] = embeddings[i]
        
        return documents

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a query.

        Args:
            query: Query text.

        Returns:
            Embedding vector.
        """
        return self.embed_text(query)