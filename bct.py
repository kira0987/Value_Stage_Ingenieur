import aiohttp
import asyncio
import urllib.robotparser
import os
import PyPDF2
from bs4 import BeautifulSoup
import io
from urllib.parse import urljoin, urlparse
import time
import hashlib
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor
import backoff
import aiofiles
import json
from datetime import datetime
import re
from typing import Set, Dict, List, Optional
import asyncio
from aiohttp import ClientTimeout, TCPConnector
from aiohttp.client_exceptions import ClientError, ServerTimeoutError

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://www.bct.gov.tn/bct/siteprod/actualites.jsp?id="
RESULT_DIR = "result"
PDFS_DIR = os.path.join(RESULT_DIR, "pdfs")
TEXT_DIR = os.path.join(RESULT_DIR, "text")
METADATA_FILE = os.path.join(RESULT_DIR, "metadata.json")
BATCH_SIZE = 50
MAX_RETRIES = 3
RATE_LIMIT_DELAY = 1  # seconds
TIMEOUT = 30  # seconds

# Headers to mimic a browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

class PDFProcessor:
    def __init__(self):
        self.downloaded_pdfs: Set[str] = set()
        self.metadata: Dict[str, Dict] = {}
        self.load_metadata()

    def load_metadata(self):
        try:
            if os.path.exists(METADATA_FILE):
                with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                    self.downloaded_pdfs = set(self.metadata.keys())
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            self.metadata = {}

    def save_metadata(self):
        try:
            with open(METADATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")

    def get_unique_pdf_filename(self, pdf_url: str, content: bytes) -> str:
        parsed_url = urlparse(pdf_url)
        original_filename = os.path.basename(parsed_url.path)
        if not original_filename.endswith('.pdf'):
            original_filename = 'document.pdf'
        
        content_hash = hashlib.md5(content).hexdigest()[:8]
        filename = f"{os.path.splitext(original_filename)[0]}_{content_hash}.pdf"
        return filename

    def is_valid_pdf(self, content: bytes) -> bool:
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            return len(pdf_reader.pages) > 0
        except Exception as e:
            logger.debug(f"Invalid PDF content: {e}")
            return False

    async def save_pdf(self, content: bytes, pdf_url: str) -> bool:
        content_hash = hashlib.md5(content).hexdigest()
        if content_hash in self.downloaded_pdfs:
            logger.debug(f"PDF already downloaded: {pdf_url}")
            return False

        try:
            filename = self.get_unique_pdf_filename(pdf_url, content)
            pdf_path = os.path.join(PDFS_DIR, filename)
            
            async with aiofiles.open(pdf_path, 'wb') as f:
                await f.write(content)

            # Update metadata
            self.metadata[content_hash] = {
                'url': pdf_url,
                'filename': filename,
                'download_date': datetime.now().isoformat(),
                'size': len(content)
            }
            self.downloaded_pdfs.add(content_hash)
            self.save_metadata()
            
            logger.info(f"Saved PDF: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving PDF {pdf_url}: {e}")
            return False

class Scraper:
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.semaphore = asyncio.Semaphore(10)  # Limit concurrent connections
        self.rate_limiter = asyncio.Lock()

    def find_pdf_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        pdf_links = set()
        
        # Find direct PDF links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.lower().endswith('.pdf'):
                pdf_links.add(urljoin(base_url, href))
        
        # Find links that might contain PDFs
        pdf_keywords = ['document', 'pdf', 'download', 'file', 'rapport', 'publication']
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if any(keyword in href for keyword in pdf_keywords):
                pdf_links.add(urljoin(base_url, link['href']))
        
        return pdf_links

    @backoff.on_exception(
        backoff.expo,
        (ClientError, ServerTimeoutError, asyncio.TimeoutError),
        max_tries=MAX_RETRIES
    )
    async def fetch_url(self, session: aiohttp.ClientSession, url: str) -> Optional[bytes]:
        async with self.semaphore:
            async with self.rate_limiter:
                await asyncio.sleep(RATE_LIMIT_DELAY)
                
            try:
                async with session.get(url, headers=headers, timeout=TIMEOUT) as response:
                    if response.status == 200:
                        return await response.read()
                    logger.warning(f"Failed to fetch {url}: Status {response.status}")
                    return None
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                raise

    async def process_url(self, session: aiohttp.ClientSession, url: str):
        try:
            content = await self.fetch_url(session, url)
            if not content:
                return

            content_type = session.headers.get("Content-Type", "").lower()
            
            # Check if direct PDF
            if "application/pdf" in content_type or url.lower().endswith('.pdf'):
                if self.pdf_processor.is_valid_pdf(content):
                    await self.pdf_processor.save_pdf(content, url)
                return

            # Parse HTML and look for PDFs
            soup = BeautifulSoup(content, 'html.parser')
            pdf_links = self.find_pdf_links(soup, url)

            # Process each PDF link
            for pdf_url in pdf_links:
                try:
                    pdf_content = await self.fetch_url(session, pdf_url)
                    if pdf_content and self.pdf_processor.is_valid_pdf(pdf_content):
                        await self.pdf_processor.save_pdf(pdf_content, pdf_url)
                except Exception as e:
                    logger.error(f"Error processing PDF link {pdf_url}: {e}")

        except Exception as e:
            logger.error(f"Error processing {url}: {e}")

    async def scrape(self):
        # Create directories
        os.makedirs(PDFS_DIR, exist_ok=True)
        os.makedirs(TEXT_DIR, exist_ok=True)

        # Configure aiohttp session
        connector = TCPConnector(limit=10, force_close=True)
        timeout = ClientTimeout(total=TIMEOUT)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            for id in range(1, 1201):
                url = f"{BASE_URL}{id}"
                task = asyncio.create_task(self.process_url(session, url))
                tasks.append(task)
                
                if len(tasks) >= BATCH_SIZE:
                    await asyncio.gather(*tasks)
                    tasks = []
                    logger.info(f"Processed batch of {BATCH_SIZE} URLs")
            
            if tasks:
                await asyncio.gather(*tasks)
                logger.info("Processed remaining URLs")

async def main():
    scraper = Scraper()
    await scraper.scrape()

if __name__ == "__main__":
    asyncio.run(main())