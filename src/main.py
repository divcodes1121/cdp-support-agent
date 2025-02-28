"""
Main entry point for the CDP Support Agent Chatbot.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from src.config import (
    RAW_DATA_DIR, 
    PROCESSED_DATA_DIR, 
    VECTOR_DB_PATH, 
    API_HOST,
    API_PORT,
    DEBUG_MODE
)
from src.scraper.scraper import scrape_all_cdps
from src.indexer.vectorstore import process_and_index_documents, VectorStore
from src.retriever.retriever import DocumentRetriever, ComparisonRetriever
from src.chatbot.query_processor import QueryProcessor
from src.chatbot.response_generator import ResponseGenerator
from src.api.routes import create_app

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def setup_application():
    """
    Set up the application components.
    
    Returns:
        Flask application instance.
    """
    # Initialize vector store
    vector_store = VectorStore(db_path=VECTOR_DB_PATH)
    
    # Check if vector store is empty
    stats = vector_store.get_collection_stats()
    if stats.get("document_count", 0) == 0:
        logger.warning("Vector store is empty. Run scraping and indexing first.")
    
    # Initialize retrievers
    document_retriever = DocumentRetriever(vector_store)
    comparison_retriever = ComparisonRetriever(vector_store)
    
    # Initialize query processor and response generator
    query_processor = QueryProcessor(document_retriever, comparison_retriever)
    response_generator = ResponseGenerator()
    
    # Create Flask application
    app = create_app(query_processor, response_generator)
    
    return app


def scrape_and_index():
    """
    Run scraping and indexing process.
    """
    logger.info("Starting scraping process...")
    scrape_all_cdps(max_pages_per_cdp=50)
    
    logger.info("Starting indexing process...")
    process_and_index_documents(raw_data_dir=RAW_DATA_DIR)
    
    logger.info("Scraping and indexing completed successfully.")


def run_server():
    """
    Run the web server.
    """
    app = setup_application()
    logger.info(f"Starting server on {API_HOST}:{API_PORT}...")
    app.run(host=API_HOST, port=API_PORT, debug=DEBUG_MODE)


def main():
    """
    Main entry point.
    """
    parser = argparse.ArgumentParser(description="CDP Support Agent Chatbot")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Scrape and index command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape and index CDP documentation")
    
    # Run server command
    server_parser = subparsers.add_parser("serve", help="Run the web server")
    
    args = parser.parse_args()
    
    if args.command == "scrape":
        scrape_and_index()
    elif args.command == "serve":
        run_server()
    else:
        # Default to running the server
        run_server()


if __name__ == "__main__":
    main()