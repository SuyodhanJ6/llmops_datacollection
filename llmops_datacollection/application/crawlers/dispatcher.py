import re
from urllib.parse import urlparse

from loguru import logger

from .base import BaseCrawler
from .linkedin import LinkedInCrawler
from .medium import MediumCrawler
from .github import GithubCrawler

class CrawlerDispatcher:
    """Dispatcher for selecting appropriate crawler based on URL."""
    
    def __init__(self):
        self._crawlers = {}
        
    @classmethod
    def build(cls) -> "CrawlerDispatcher":
        """Build dispatcher with default crawlers."""
        dispatcher = cls()
        dispatcher.register("linkedin.com", LinkedInCrawler)
        dispatcher.register("medium.com", MediumCrawler)
        dispatcher.register("github.com", GithubCrawler)
        return dispatcher
        
    def register(self, domain: str, crawler_class: type[BaseCrawler]) -> None:
        """Register a crawler for a domain."""
        # Create regex pattern for domain
        pattern = r"https://(www\.)?{}/*".format(
            re.escape(urlparse(domain).netloc or domain)
        )
        self._crawlers[pattern] = crawler_class
        
    def get_crawler(self, url: str) -> BaseCrawler:
        """Get appropriate crawler for URL."""
        for pattern, crawler_class in self._crawlers.items():
            if re.match(pattern, url):
                return crawler_class()
                
        logger.warning(f"No crawler found for {url}")
        raise ValueError(f"Unsupported URL: {url}")

    def crawl_urls(self, urls: list[str], **kwargs) -> None:
        """Crawl multiple URLs."""
        for url in urls:
            try:
                crawler = self.get_crawler(url)
                crawler.extract(url, **kwargs)
            except Exception as e:
                logger.error(f"Failed to crawl {url}: {str(e)}")