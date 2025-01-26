from bs4 import BeautifulSoup
from loguru import logger
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from llmops_datacollection.domain.documents import ArticleDocument
from llmops_datacollection.domain.exceptions import CrawlerError
from .base import BaseSeleniumCrawler

class MediumCrawler(BaseSeleniumCrawler):
    """Medium article crawler."""
    
    model = ArticleDocument

    def extract(self, link: str, **kwargs) -> None:
        """Extract article from Medium."""
        if self.model.find(link=link):
            logger.info(f"Article already exists: {link}")
            return

        logger.info(f"Extracting article: {link}")

        try:
            # Navigate to article
            self.driver.get(link)
            
            # Wait for article content to load
            try:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "article"))
                )
            except TimeoutException:
                raise CrawlerError("Article content not found")
            
            # Scroll to load full content
            self.scroll_page()

            # Parse content
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            
            # Extract article components
            title = self._extract_title(soup)
            subtitle = self._extract_subtitle(soup)
            content = self._extract_content(soup)
            
            # Create article data
            article_data = {
                "title": title,
                "subtitle": subtitle,
                "content": content,
                "metadata": {
                    "reading_time": self._extract_reading_time(soup),
                    "claps": self._extract_claps(soup),
                }
            }

            # Save article
            user = kwargs["user"]
            article = self.model(
                platform="medium",
                content=article_data,
                link=link,
                title=title,
                author_id=user.id,
                author_full_name=user.full_name,
            )
            article.save()

            logger.info("Successfully extracted article")

        except Exception as e:
            logger.error(f"Failed to extract article: {str(e)}")
            raise CrawlerError(f"Article extraction failed: {str(e)}")
        finally:
            self.driver.quit()

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title."""
        if title_elem := soup.find("h1", class_="pw-post-title"):
            return title_elem.text.strip()
        return "Untitled"

    def _extract_subtitle(self, soup: BeautifulSoup) -> str | None:
        """Extract article subtitle."""
        if subtitle_elem := soup.find("h2", class_="pw-subtitle-paragraph"):
            return subtitle_elem.text.strip()
        return None

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract article content."""
        if article := soup.find("article"):
            # Remove script and style elements
            for element in article.find_all(["script", "style"]):
                element.decompose()
            return article.get_text(separator="\n\n", strip=True)
        return ""

    def _extract_reading_time(self, soup: BeautifulSoup) -> int:
        """Extract reading time in minutes."""
        try:
            if time_elem := soup.find("span", {"aria-label": "Post reading time"}):
                return int(time_elem.text.split()[0])
        except (ValueError, AttributeError, IndexError):
            pass
        return 0

    def _extract_claps(self, soup: BeautifulSoup) -> int:
        """Extract number of claps."""
        try:
            if claps_elem := soup.find("button", {"aria-label": "clap"}):
                return int(claps_elem.text.strip())
        except (ValueError, AttributeError):
            pass
        return 0