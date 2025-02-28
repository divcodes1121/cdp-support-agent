"""
Document indexing module for CDP documentation.
"""

from src.indexer.embeddings import DocumentEmbedder
from src.indexer.vectorstore import VectorStore, process_and_index_documents

__all__ = [
    'DocumentEmbedder',
    'VectorStore',
    'process_and_index_documents'
]