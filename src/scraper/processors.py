"""
Text processing utilities for the CDP documentation.
"""

import re
from typing import List, Dict

import html2text
import nltk
from bs4 import BeautifulSoup


# Download required NLTK data
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")


def clean_html_content(html_content: str) -> str:
    """
    Clean HTML content and convert to formatted text.

    Args:
        html_content: HTML content to clean.

    Returns:
        Cleaned and formatted text.
    """
    # Use html2text to convert HTML to markdown-formatted text
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = False
    converter.ignore_tables = False
    converter.body_width = 0  # Don't wrap lines
    
    text = converter.handle(html_content)
    
    # Remove excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # Remove JavaScript and CSS code blocks
    text = re.sub(r"```javascript[\s\S]*?```", "", text)
    text = re.sub(r"```css[\s\S]*?```", "", text)
    
    return text.strip()


def split_text_into_chunks(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks for indexing.

    Args:
        text: Text to split.
        chunk_size: Maximum size of each chunk.
        chunk_overlap: Overlap between consecutive chunks.

    Returns:
        List of text chunks.
    """
    # Use NLTK to split text into sentences
    sentences = nltk.sent_tokenize(text)
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_size = len(sentence)
        
        # If adding this sentence would exceed chunk size, finalize the chunk
        if current_size + sentence_size > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            
            # Keep the last sentences for overlap
            overlap_size = 0
            overlap_sentences = []
            
            for s in reversed(current_chunk):
                if overlap_size + len(s) <= chunk_overlap:
                    overlap_sentences.insert(0, s)
                    overlap_size += len(s)
                else:
                    break
            
            current_chunk = overlap_sentences
            current_size = overlap_size
        
        # Add the current sentence to the chunk
        current_chunk.append(sentence)
        current_size += sentence_size
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks


def extract_metadata(data: Dict) -> Dict:
    """
    Extract metadata from a document.

    Args:
        data: Document data with content and metadata.

    Returns:
        Extracted metadata.
    """
    # Extract platform information
    platform = data.get("platform", "unknown")
    
    # Extract title
    title = data.get("title", "")
    
    # Extract URL
    url = data.get("url", "")
    
    # Extract headings for context
    headings = data.get("headings", [])
    
    # Build heading hierarchy
    heading_hierarchy = []
    current_level = 0
    current_hierarchy = []
    
    for heading in headings:
        level = heading.get("level", 0)
        text = heading.get("text", "")
        
        # Reset hierarchy if we go to a higher level
        if level <= current_level:
            current_hierarchy = current_hierarchy[:level-1]
        
        current_hierarchy.append(text)
        current_level = level
        heading_hierarchy.append(" > ".join(current_hierarchy))
    
    # Determine document type based on title and content
    doc_type = "unknown"
    if "how to" in title.lower() or "guide" in title.lower():
        doc_type = "how-to"
    elif "api" in title.lower() or "reference" in title.lower():
        doc_type = "reference"
    elif "overview" in title.lower() or "introduction" in title.lower():
        doc_type = "overview"
    
    return {
        "platform": platform,
        "title": title,
        "url": url,
        "heading_hierarchy": heading_hierarchy,
        "doc_type": doc_type
    }


def prepare_document_chunks(data: Dict, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Dict]:
    """
    Prepare document chunks for indexing.

    Args:
        data: Document data with content and metadata.
        chunk_size: Maximum size of each chunk.
        chunk_overlap: Overlap between consecutive chunks.

    Returns:
        List of document chunks with metadata.
    """
    content = data.get("content", "")
    metadata = extract_metadata(data)
    
    # Split content into chunks
    chunks = split_text_into_chunks(content, chunk_size, chunk_overlap)
    
    # Prepare document chunks with metadata
    document_chunks = []
    for i, chunk in enumerate(chunks):
        chunk_data = {
            "content": chunk,
            "chunk_id": f"{metadata['platform']}_{i}",
            "metadata": metadata
        }
        document_chunks.append(chunk_data)
    
    return document_chunks