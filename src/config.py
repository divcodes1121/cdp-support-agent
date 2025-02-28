"""
Configuration settings for the CDP Support Agent Chatbot.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Create directories if they don't exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# CDP documentation URLs
CDP_DOCS = {
    "segment": "https://segment.com/docs/?ref=nav",
    "mparticle": "https://docs.mparticle.com/",
    "lytics": "https://docs.lytics.com/",
    "zeotap": "https://docs.zeotap.com/home/en-us/"
}

# Vector database settings
VECTOR_DB_PATH = PROCESSED_DATA_DIR / "vector_db"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 5000))
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

# Retrieval settings
TOP_K_RESULTS = 5
SIMILARITY_THRESHOLD = 0.7

# Selenium settings
SELENIUM_WAIT_TIME = 10  # seconds
HEADLESS_BROWSER = True