import os
import json
from pathlib import Path
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the necessary functions
from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, VECTOR_DB_PATH
from src.indexer.vectorstore import VectorStore
from src.scraper.processors import prepare_document_chunks

# Set up paths
raw_dir = Path("data/raw")
processed_dir = Path("data/processed")
vector_db_path = processed_dir / "vector_db"

# Make sure directories exist
processed_dir.mkdir(exist_ok=True)
vector_db_path.mkdir(exist_ok=True, parents=True)

logger.info("Initializing vector store...")
vector_store = VectorStore(db_path=vector_db_path)

# Process all CDP data
all_document_chunks = []

# Get all CDP directories
cdp_dirs = [d for d in raw_dir.iterdir() if d.is_dir()]

for cdp_dir in cdp_dirs:
    cdp_name = cdp_dir.name
    logger.info(f"Processing data for {cdp_name}")
    
    # Get all JSON files
    json_files = list(cdp_dir.glob("*.json"))
    
    for json_file in tqdm(json_files, desc=f"Processing {cdp_name} documents"):
        try:
            # Load document data
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Prepare document chunks
            document_chunks = prepare_document_chunks(data)
            all_document_chunks.extend(document_chunks)
        except Exception as e:
            logger.error(f"Error processing {json_file}: {e}")

# Add documents to vector store
logger.info(f"Adding {len(all_document_chunks)} document chunks to vector store")
vector_store.add_documents(all_document_chunks)

logger.info("Processing and indexing completed successfully!")
