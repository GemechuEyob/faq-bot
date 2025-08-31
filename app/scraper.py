import logging
import traceback
import urllib.parse
from typing import List

import numpy as np
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from robotexclusionrulesparser import RobotExclusionRulesParser
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import ScrapedData
from .embedder import embedder

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize robot parser
robot_parser = RobotExclusionRulesParser()


def check_robots_txt(url: str) -> bool:
    """
    Check if scraping is allowed by robots.txt
    Returns True if scraping is allowed, False otherwise
    """
    if not settings.respect_robots_txt:
        return True  # Skip robots.txt check if disabled

    try:
        parsed_url = urllib.parse.urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

        # Fetch and parse robots.txt
        robot_parser.fetch(robots_url)

        # Check if user-agent is allowed to fetch the URL
        return robot_parser.is_allowed("*", url)
    except Exception as e:
        logger.warning(f"Error checking robots.txt for {url}: {str(e)}")
        return True  # Default to allowing if there's an error checking robots.txt


def clean_text(html_content: str) -> str:
    """Clean HTML content to get meaningful text"""
    soup = BeautifulSoup(html_content, "lxml")

    # Remove script and style elements
    for tag in soup(["script", "style"]):
        tag.decompose()

    # Get text and clean whitespace
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = " ".join(chunk for chunk in chunks if chunk)

    return text


def check_similarity(
    db: Session, url: str, embedding: List[float], threshold: float = 0.85
) -> bool:
    """Check similarity using pgvector's native operator"""
    try:
        # Ensure embedding is a 1D array
        if isinstance(embedding, list):
            embedding = np.array(embedding, dtype=np.float32)

        # Ensure it's 1D and contiguous
        embedding = np.ascontiguousarray(embedding).reshape(-1).astype(np.float32)

        # Using the <=> operator for cosine distance
        # 1 - cosine distance = cosine similarity
        # TODO: i keep getting the error  Similarity check error: (builtins.ValueError) expected ndim to be 1 here. fix the issue
        query = (
            select(
                (1 - (ScrapedData.embedding.op("<=>")(embedding))).label("similarity")
            )
            .where(ScrapedData.url == url)
            .order_by(ScrapedData.scraped_at.desc())
            .limit(1)
        )

        result = db.execute(query, {"embedding": embedding}).first()

        if result:
            similarity = result[0]
            logger.info(f"Similarity score for {url}: {similarity}")
            return similarity > threshold

        return False
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Similarity check error: {str(e)}")
        return False


def scrape_url(url: str, db: Session) -> bool:
    """
    Scrape URL and store if content is sufficiently different.
    Returns True if new content was stored.
    """
    try:
        # Check robots.txt first
        if not check_robots_txt(url):
            logger.warning(f"Skipping {url} - disallowed by robots.txt")
            return False

        # TODO: find better way to scrape and store data with better chunking strategy
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=settings.browser_headless)
            page = browser.new_page()

            logger.info(f"Scraping {url}")
            page.goto(url, timeout=settings.scrape_timeout_seconds * 1000)
            content = page.content()
            browser.close()

            cleaned_content = clean_text(content)

            embedding = embedder.generate(cleaned_content)

            if check_similarity(db, url, embedding, settings.similarity_threshold):
                logger.info(f"Content too similar for {url}")
                return False

            scraped = ScrapedData(url=url, content=cleaned_content, embedding=embedding)

            db.add(scraped)
            db.commit()
            logger.info(f"Successfully scraped {url}")
            return True

    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error scraping {url}: {str(e)}")
        return False
