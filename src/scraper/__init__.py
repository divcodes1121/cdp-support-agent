"""
Web scraping module for CDP documentation.
"""

from src.scraper.scraper import CDPScraper, scrape_all_cdps
from src.scraper.processors import (
    clean_html_content,
    split_text_into_chunks,
    extract_metadata,
    prepare_document_chunks
)

__all__ = [
    'CDPScraper',
    'scrape_all_cdps',
    'clean_html_content',
    'split_text_into_chunks',
    'extract_metadata',
    'prepare_document_chunks'
]