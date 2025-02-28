import os
import json
import requests
import time
import re
from pathlib import Path
from tqdm import tqdm
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# CDP documentation URLs
CDP_DOCS = {
    "segment": "https://segment.com/docs/?ref=nav",
    "mparticle": "https://docs.mparticle.com/",
    "lytics": "https://docs.lytics.com/",
    "zeotap": "https://docs.zeotap.com/home/en-us/"
}

# Create data directory
data_dir = Path("data")
os.makedirs(data_dir, exist_ok=True)

def clean_text(text):
    """Clean and normalize text."""
    # Replace newlines with spaces
    text = re.sub(r'\n+', ' ', text)
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_links(soup, current_url, domain):
    """Extract links from a page."""
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Skip anchors
        if href.startswith('#'):
            continue
        # Construct absolute URL
        absolute_url = href if href.startswith('http') else f"{current_url.rstrip('/')}/{href.lstrip('/')}"
        # Keep only links from the same domain
        if domain in absolute_url:
            links.append(absolute_url)
    return list(set(links))  # Remove duplicates

def scrape_page(url, platform):
    """Scrape a single page."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text() if title else "Untitled"
        
        # Extract content
        content = ""
        
        # Try to find main content areas
        main_content = None
        for selector in ['main', 'article', '.content', '.documentation', '#content', '#main-content', '.main-content']:
            if selector.startswith('.'):
                element = soup.select_one(selector)
            elif selector.startswith('#'):
                element = soup.find(id=selector[1:])
            else:
                element = soup.find(selector)
                
            if element:
                main_content = element
                break
        
        # If no specific content area found, use the body
        if not main_content:
            main_content = soup.find('body')
        
        # Extract text from paragraphs, headings, and list items
        for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
            content += element.get_text() + "\n\n"
        
        # Clean content
        content = clean_text(content)
        
        # Extract headings for structure
        headings = []
        for h in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            h_text = h.get_text().strip()
            if h_text:
                headings.append({
                    'level': int(h.name[1]),
                    'text': h_text
                })
        
        return {
            'url': url,
            'title': title_text,
            'content': content,
            'headings': headings,
            'platform': platform
        }
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return None

def scrape_cdp(platform_name, start_url, max_pages=30):
    """Scrape CDP documentation."""
    logger.info(f"Starting scrape for {platform_name}...")
    
    # Create platform directory
    platform_dir = data_dir / platform_name
    os.makedirs(platform_dir, exist_ok=True)
    
    # Extract domain from URL
    domain = re.search(r'https?://([^/]+)', start_url).group(1)
    
    to_visit = [start_url]
    visited = set()
    scraped_pages = 0
    
    with tqdm(total=max_pages, desc=f"Scraping {platform_name}") as pbar:
        while to_visit and scraped_pages < max_pages:
            # Get the next URL
            current_url = to_visit.pop(0)
            
            # Skip if already visited
            if current_url in visited:
                continue
            
            # Mark as visited
            visited.add(current_url)
            
            # Scrape the page
            page_data = scrape_page(current_url, platform_name)
            
            if page_data:
                # Save the page data
                file_name = f"page_{scraped_pages}.json"
                with open(platform_dir / file_name, 'w', encoding='utf-8') as f:
                    json.dump(page_data, f, ensure_ascii=False, indent=2)
                
                # Extract links from the page
                soup = BeautifulSoup(requests.get(current_url).text, 'html.parser')
                new_links = extract_links(soup, current_url, domain)
                
                # Add new links to visit
                for link in new_links:
                    if link not in visited and link not in to_visit:
                        to_visit.append(link)
                
                # Update progress
                scraped_pages += 1
                pbar.update(1)
            
            # Be nice to the server
            time.sleep(1)
    
    logger.info(f"Completed scrape for {platform_name}. Scraped {scraped_pages} pages.")

def scrape_all_cdps(max_pages_per_cdp=30):
    """Scrape all CDPs."""
    for platform, url in CDP_DOCS.items():
        scrape_cdp(platform, url, max_pages=max_pages_per_cdp)

if __name__ == "__main__":
    scrape_all_cdps()
