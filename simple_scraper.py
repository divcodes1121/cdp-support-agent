import os
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

# Create data directories
data_dir = Path("data")
raw_dir = data_dir / "raw"
os.makedirs(raw_dir, exist_ok=True)

# CDP documentation URLs
cdp_docs = {
    "segment": "https://segment.com/docs/?ref=nav",
    "mparticle": "https://docs.mparticle.com/",
    "lytics": "https://docs.lytics.com/",
    "zeotap": "https://docs.zeotap.com/home/en-us/"
}

def scrape_page(url, platform):
    print(f"Scraping {url}...")
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.text if title else "Untitled"
        
        # Extract content
        content = ""
        for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li']):
            content += p.get_text() + "\n\n"
        
        return {
            "url": url,
            "title": title_text,
            "content": content,
            "platform": platform,
            "headings": [
                {"level": 1, "text": title_text}
            ]
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

# Scrape main pages
for platform, url in cdp_docs.items():
    platform_dir = raw_dir / platform
    os.makedirs(platform_dir, exist_ok=True)
    
    data = scrape_page(url, platform)
    if data:
        with open(platform_dir / "index.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Completed scraping basic content for {platform}")

print("Basic scraping completed! You can now run the indexing process.")
