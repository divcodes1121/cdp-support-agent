"""
Web scraper for CDP documentation websites.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager

from src.config import CDP_DOCS, HEADLESS_BROWSER, RAW_DATA_DIR, SELENIUM_WAIT_TIME
from src.scraper.processors import clean_html_content

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class CDPScraper:
    """
    Scraper for CDP documentation websites.
    """

    def __init__(self, cdp_name: str, base_url: str):
        """
        Initialize the scraper.

        Args:
            cdp_name: Name of the CDP to scrape.
            base_url: Base URL of the CDP documentation.
        """
        self.cdp_name = cdp_name
        self.base_url = base_url
        self.visited_urls: Set[str] = set()
        self.data_dir = RAW_DATA_DIR / cdp_name
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Set up Selenium
        chrome_options = Options()
        if HEADLESS_BROWSER:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options,
        )
        self.wait = WebDriverWait(self.driver, SELENIUM_WAIT_TIME)

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and within the documentation domain."""
        if not url or url in self.visited_urls:
            return False

        # Check if URL is absolute and belongs to the same domain
        parsed_base = urlparse(self.base_url)
        parsed_url = urlparse(url)
        
        if not parsed_url.netloc:  # Relative URL
            return True
        
        # Check if URL belongs to the same domain
        return parsed_base.netloc == parsed_url.netloc

    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """
        Get the content of a page using Selenium.

        Args:
            url: URL to fetch.

        Returns:
            BeautifulSoup object or None if failed.
        """
        try:
            self.driver.get(url)
            # Wait for page to load
            self.wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            # Allow for JavaScript to render
            time.sleep(2)
            
            html_content = self.driver.page_source
            return BeautifulSoup(html_content, "html.parser")
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def extract_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """
        Extract links from a BeautifulSoup object.

        Args:
            soup: BeautifulSoup object.
            current_url: Current URL to resolve relative links.

        Returns:
            List of URLs.
        """
        links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            # Skip anchors within the same page
            if href.startswith("#"):
                continue
                
            # Resolve relative URLs
            absolute_url = urljoin(current_url, href)
            
            # Only include valid URLs
            if self.is_valid_url(absolute_url):
                links.append(absolute_url)
                
        return links

    def extract_content(self, soup: BeautifulSoup, url: str) -> Dict:
        """
        Extract content from a BeautifulSoup object.

        Args:
            soup: BeautifulSoup object.
            url: URL of the page.

        Returns:
            Dictionary with page metadata and content.
        """
        # Find the main content area - this may need adjustment for different sites
        main_content = None
        
        # Look for common content containers
        content_selectors = [
            "main", "article", ".content", ".documentation", 
            "#content", "#main-content", ".main-content"
        ]
        
        for selector in content_selectors:
            if selector.startswith(".") or selector.startswith("#"):
                element = soup.select_one(selector)
            else:
                element = soup.find(selector)
                
            if element:
                main_content = element
                break
        
        # If no content container found, use the body
        if not main_content:
            main_content = soup.find("body")
        
        # Extract title
        title_element = soup.find("title")
        title = title_element.text if title_element else "Untitled"
        
        # Extract headings to determine context
        headings = []
        for h in soup.find_all(["h1", "h2", "h3"]):
            headings.append({"level": int(h.name[1]), "text": h.text.strip()})
        
        # Clean and extract the main content
        content_html = str(main_content) if main_content else str(soup)
        clean_content = clean_html_content(content_html)
        
        return {
            "url": url,
            "title": title,
            "headings": headings,
            "content": clean_content,
            "platform": self.cdp_name,
        }

    def save_content(self, data: Dict, url: str) -> None:
        """
        Save content to a JSON file.

        Args:
            data: Content data.
            url: URL of the page.
        """
        # Create a filename from the URL
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip("/").split("/")
        
        # Use the last part of the path, or 'index' if empty
        filename = path_parts[-1] if path_parts else "index"
        if not filename:
            filename = "index"
        
        # Add a suffix if there are query parameters
        if parsed_url.query:
            filename = f"{filename}_{hash(parsed_url.query)}"
        
        # Ensure the filename is valid
        filename = filename.replace(".", "_")
        if not filename.endswith(".json"):
            filename = f"{filename}.json"
        
        # Save to JSON file
        file_path = self.data_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {url} to {file_path}")

    def crawl(self, start_url: Optional[str] = None, max_pages: int = 100) -> None:
        """
        Crawl the CDP documentation starting from the base or specified URL.

        Args:
            start_url: URL to start crawling from (defaults to base_url).
            max_pages: Maximum number of pages to crawl.
        """
        if not start_url:
            start_url = self.base_url
            
        urls_to_visit = [start_url]
        page_count = 0
        
        with tqdm(total=max_pages, desc=f"Crawling {self.cdp_name}") as pbar:
            while urls_to_visit and page_count < max_pages:
                current_url = urls_to_visit.pop(0)
                
                # Skip if already visited
                if current_url in self.visited_urls:
                    continue
                    
                logger.info(f"Crawling: {current_url}")
                
                # Mark as visited
                self.visited_urls.add(current_url)
                
                # Get page content
                soup = self.get_page_content(current_url)
                if not soup:
                    continue
                
                # Extract content
                page_data = self.extract_content(soup, current_url)
                
                # Save content
                self.save_content(page_data, current_url)
                
                # Extract links and add to queue
                links = self.extract_links(soup, current_url)
                for link in links:
                    if link not in self.visited_urls and link not in urls_to_visit:
                        urls_to_visit.append(link)
                
                page_count += 1
                pbar.update(1)
                
                # Add a small delay to be polite to the server
                time.sleep(1)
        
        logger.info(f"Crawling completed. Visited {page_count} pages.")

    def close(self) -> None:
        """Close the Selenium driver."""
        if hasattr(self, "driver"):
            self.driver.quit()


def scrape_all_cdps(max_pages_per_cdp: int = 100) -> None:
    """
    Scrape documentation for all CDPs.

    Args:
        max_pages_per_cdp: Maximum number of pages to crawl per CDP.
    """
    for cdp_name, base_url in CDP_DOCS.items():
        logger.info(f"Starting scrape for {cdp_name}...")
        scraper = CDPScraper(cdp_name, base_url)
        
        try:
            scraper.crawl(max_pages=max_pages_per_cdp)
        except Exception as e:
            logger.error(f"Error scraping {cdp_name}: {e}")
        finally:
            scraper.close()
            
        logger.info(f"Completed scrape for {cdp_name}")


if __name__ == "__main__":
    scrape_all_cdps()