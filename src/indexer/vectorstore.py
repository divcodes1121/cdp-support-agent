"""
Vector database for storing and retrieving document embeddings.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from langchain.vectorstores import Chroma
from langchain.embeddings.base import Embeddings
from langchain.docstore.document import Document
from tqdm import tqdm

from src.config import VECTOR_DB_PATH, EMBEDDING_MODEL
from src.indexer.embeddings import DocumentEmbedder

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class VectorStore:
    """
    Vector database for storing and retrieving document embeddings.
    """

    def __init__(
        self, 
        db_path: Path = VECTOR_DB_PATH, 
        embedding_model: str = EMBEDDING_MODEL
    ):
        """
        Initialize the vector database.

        Args:
            db_path: Path to the vector database.
            embedding_model: Name of the embedding model to use.
        """
        self.db_path = db_path
        self.embedding_model = embedding_model
        
        # Create directory if it doesn't exist
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize document embedder
        self.embedder = DocumentEmbedder(model_name=embedding_model)
        
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Create or get collection for CDP documentation
        self.collection = self.client.get_or_create_collection(
            name="cdp_documentation",
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=embedding_model
            ),
            metadata={"description": "CDP documentation chunks with embeddings"}
        )
        
        # Initialize LangChain vector store
        self.langchain_store = Chroma(
            collection_name="cdp_documentation",
            embedding_function=self.embedder.embeddings,
            persist_directory=str(db_path)
        )
        
        logger.info(f"Vector store initialized at {db_path}")
    
    def add_documents(self, documents: List[Dict]) -> None:
        """
        Add documents to the vector database.

        Args:
            documents: List of document chunks with content and metadata.
        """
        # Prepare data for the collection
        ids = []
        texts = []
        metadatas = []
        
        for doc in documents:
            doc_id = doc.get("chunk_id", f"doc_{len(ids)}")
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            
            ids.append(doc_id)
            texts.append(content)
            metadatas.append(metadata)
        
        # Add documents to collection in batches
        batch_size = 100
        for i in tqdm(range(0, len(ids), batch_size), desc="Adding documents to vector store"):
            batch_ids = ids[i:i+batch_size]
            batch_texts = texts[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            
            try:
                self.collection.add(
                    ids=batch_ids,
                    documents=batch_texts,
                    metadatas=batch_metadatas
                )
            except Exception as e:
                logger.error(f"Error adding batch to collection: {e}")
        
        logger.info(f"Added {len(ids)} documents to the vector store")
    
    def query(
        self, 
        query_text: str, 
        n_results: int = 5, 
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        Query the vector database.

        Args:
            query_text: Query text.
            n_results: Number of results to return.
            filter_dict: Optional filter for the query.

        Returns:
            List of document chunks matching the query.
        """
        # Execute the query
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=filter_dict
            )
            
            # Format the results
            formatted_results = []
            for i in range(len(results.get("documents", [[]])[0])):
                formatted_results.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "id": results["ids"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            return []
    
    def query_langchain(
        self, 
        query_text: str, 
        n_results: int = 5, 
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Query the vector database using LangChain.

        Args:
            query_text: Query text.
            n_results: Number of results to return.
            filter_dict: Optional filter for the query.

        Returns:
            List of LangChain Document objects matching the query.
        """
        try:
            return self.langchain_store.similarity_search(
                query=query_text,
                k=n_results,
                filter=filter_dict
            )
        except Exception as e:
            logger.error(f"Error querying vector store with LangChain: {e}")
            return []
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict]:
        """
        Get a document by its ID.

        Args:
            doc_id: Document ID.

        Returns:
            Document data or None if not found.
        """
        try:
            result = self.collection.get(ids=[doc_id])
            
            if result["documents"]:
                return {
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0],
                    "id": result["ids"][0]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting document by ID: {e}")
            return None
    
    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the collection.

        Returns:
            Dictionary with collection statistics.
        """
        try:
            count = self.collection.count()
            return {
                "document_count": count,
                "collection_name": self.collection.name,
                "embedding_model": self.embedding_model
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {
                "document_count": 0,
                "collection_name": self.collection.name,
                "embedding_model": self.embedding_model,
                "error": str(e)
            }
    
    def reset_collection(self) -> None:
        """Reset the collection by deleting all documents."""
        try:
            self.collection.delete(where={})
            logger.info("Collection reset successfully")
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")


def process_and_index_documents(
    raw_data_dir: Path, 
    db_path: Path = VECTOR_DB_PATH,
    embedding_model: str = EMBEDDING_MODEL,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> None:
    """
    Process raw documents and index them in the vector database.

    Args:
        raw_data_dir: Directory containing raw document data.
        db_path: Path to the vector database.
        embedding_model: Name of the embedding model to use.
        chunk_size: Maximum size of each chunk.
        chunk_overlap: Overlap between consecutive chunks.
    """
    from src.scraper.processors import prepare_document_chunks
    
    logger.info(f"Processing and indexing documents from {raw_data_dir}")
    
    # Initialize vector store
    vector_store = VectorStore(db_path=db_path, embedding_model=embedding_model)
    
    # Get all CDP subdirectories
    cdp_dirs = [d for d in raw_data_dir.iterdir() if d.is_dir()]
    
    all_document_chunks = []
    
    # Process each CDP's documents
    for cdp_dir in cdp_dirs:
        cdp_name = cdp_dir.name
        logger.info(f"Processing documents for {cdp_name}")
        
        # Get all JSON files
        json_files = list(cdp_dir.glob("*.json"))
        
        for json_file in tqdm(json_files, desc=f"Processing {cdp_name} documents"):
            try:
                # Load document data
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Prepare document chunks
                document_chunks = prepare_document_chunks(
                    data,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
                
                all_document_chunks.extend(document_chunks)
            except Exception as e:
                logger.error(f"Error processing {json_file}: {e}")
    
    # Add all document chunks to the vector store
    logger.info(f"Indexing {len(all_document_chunks)} document chunks")
    vector_store.add_documents(all_document_chunks)
    
    logger.info("Document indexing completed")


if __name__ == "__main__":
    from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP
    
    process_and_index_documents(
        raw_data_dir=RAW_DATA_DIR,
        db_path=PROCESSED_DATA_DIR / "vector_db",
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )