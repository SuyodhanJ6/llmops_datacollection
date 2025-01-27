# from bs4 import BeautifulSoup
# from loguru import logger
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.by import By
# from selenium.common.exceptions import TimeoutException

# from llmops_datacollection.domain.documents import ArticleDocument
# from llmops_datacollection.domain.exceptions import CrawlerError
# from .base import BaseSeleniumCrawler

# class MediumCrawler(BaseSeleniumCrawler):
#     """Medium article crawler."""
    
#     model = ArticleDocument

#     def extract(self, link: str, **kwargs) -> None:
#         """Extract article from Medium."""
#         if self.model.find(link=link):
#             logger.info(f"Article already exists: {link}")
#             return

#         logger.info(f"Extracting article: {link}")

#         try:
#             # Navigate to article
#             self.driver.get(link)
            
#             # Wait for article content to load
#             try:
#                 WebDriverWait(self.driver, self.timeout).until(
#                     EC.presence_of_element_located((By.TAG_NAME, "article"))
#                 )
#             except TimeoutException:
#                 raise CrawlerError("Article content not found")
            
#             # Scroll to load full content
#             self.scroll_page()

#             # Parse content
#             soup = BeautifulSoup(self.driver.page_source, "html.parser")
            
#             # Extract article components
#             title = self._extract_title(soup)
#             subtitle = self._extract_subtitle(soup)
#             content = self._extract_content(soup)
            
#             # Create article data
#             article_data = {
#                 "title": title,
#                 "subtitle": subtitle,
#                 "content": content,
#                 "metadata": {
#                     "reading_time": self._extract_reading_time(soup),
#                     "claps": self._extract_claps(soup),
#                 }
#             }

#             # Save article
#             user = kwargs["user"]
#             article = self.model(
#                 platform="medium",
#                 content=article_data,
#                 link=link,
#                 title=title,
#                 author_id=user.id,
#                 author_full_name=user.full_name,
#             )
#             article.save()

#             logger.info("Successfully extracted article")

#         except Exception as e:
#             logger.error(f"Failed to extract article: {str(e)}")
#             raise CrawlerError(f"Article extraction failed: {str(e)}")
#         finally:
#             self.driver.quit()

#     def _extract_title(self, soup: BeautifulSoup) -> str:
#         """Extract article title."""
#         if title_elem := soup.find("h1", class_="pw-post-title"):
#             return title_elem.text.strip()
#         return "Untitled"

#     def _extract_subtitle(self, soup: BeautifulSoup) -> str | None:
#         """Extract article subtitle."""
#         if subtitle_elem := soup.find("h2", class_="pw-subtitle-paragraph"):
#             return subtitle_elem.text.strip()
#         return None

#     def _extract_content(self, soup: BeautifulSoup) -> str:
#         """Extract article content."""
#         if article := soup.find("article"):
#             # Remove script and style elements
#             for element in article.find_all(["script", "style"]):
#                 element.decompose()
#             return article.get_text(separator="\n\n", strip=True)
#         return ""

#     def _extract_reading_time(self, soup: BeautifulSoup) -> int:
#         """Extract reading time in minutes."""
#         try:
#             if time_elem := soup.find("span", {"aria-label": "Post reading time"}):
#                 return int(time_elem.text.split()[0])
#         except (ValueError, AttributeError, IndexError):
#             pass
#         return 0

#     def _extract_claps(self, soup: BeautifulSoup) -> int:
#         """Extract number of claps."""
#         try:
#             if claps_elem := soup.find("button", {"aria-label": "clap"}):
#                 return int(claps_elem.text.strip())
#         except (ValueError, AttributeError):
#             pass
#         return 0

# llmops_datacollection/application/crawlers/medium.py

# llmops_datacollection/application/crawlers/medium.py

from bs4 import BeautifulSoup
from loguru import logger
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time

from llmops_datacollection.domain.documents import ArticleDocument
from llmops_datacollection.domain.exceptions import CrawlerError
from .base import BaseSeleniumCrawler

class MediumCrawler(BaseSeleniumCrawler):
    """Medium article crawler."""
    
    model = ArticleDocument

    def __init__(self, scroll_limit: int = 5, timeout: int = 60):
        super().__init__(scroll_limit=scroll_limit)
        self.timeout = timeout

    def extract(self, link: str, **kwargs) -> None:
        """Extract article from Medium."""
        if self.model.find(link=link):
            logger.info(f"Article already exists: {link}")
            return

        logger.info(f"Extracting article: {link}")

        try:
            # Navigate to article
            self.driver.get(link)
            time.sleep(5)  # Wait for JavaScript content
            
            # Scroll to load dynamic content
            self.scroll_page()
            
            # Parse content
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            
            # Extract title first since it's required
            title = self._extract_title(soup)
            if not title:
                raise CrawlerError("Could not extract article title")
            
            # Extract content
            content = {
                "title": title,
                "subtitle": self._extract_subtitle(soup),
                "content": self._extract_content(soup),
                "metadata": {
                    "reading_time": self._extract_reading_time(soup),
                    "claps": self._extract_claps(soup)
                }
            }
            
            # Log extraction
            logger.info(f"Extracted title: {title}")
            logger.info(f"Content length: {len(content['content']) if content.get('content') else 0} characters")

            # Create article document
            user = kwargs["user"]
            article = self.model(
                content=content,  # This matches ContentDocument.content: dict
                platform="medium",
                link=link,
                title=title,  # This matches ArticleDocument.title requirement
                author_id=user.id,
                author_full_name=user.full_name
            )
            
            # Save article
            saved = article.save()
            if saved:
                logger.info(f"Successfully saved article: {title}")
            else:
                raise CrawlerError("Failed to save article to database")

        except Exception as e:
            logger.error(f"Failed to extract article: {str(e)}")
            raise CrawlerError(f"Article extraction failed: {str(e)}")
        finally:
            self.driver.quit()

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title."""
        selectors = [
            "h1",  
            "h1.pw-post-title",
            "h1.article-title",
            'h1[data-testid="article-title"]'
        ]
        
        for selector in selectors:
            if element := soup.select_one(selector):
                title = element.get_text(strip=True)
                if title:
                    return title
                    
        return "Untitled Article"  # Fallback title

    def _extract_subtitle(self, soup: BeautifulSoup) -> str:
        """Extract article subtitle."""
        selectors = [
            "h2.pw-subtitle-paragraph",
            "h2.article-subtitle",
            "h3.graf--subtitle",
            'h2[data-testid="article-subtitle"]'
        ]
        
        for selector in selectors:
            if element := soup.select_one(selector):
                return element.get_text(strip=True)
        return ""

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract article content."""
        # First try to find article body
        content_selectors = [
            "article",
            ".story-content",
            ".postArticle-content",
            'div[data-testid="article-body"]'
        ]
        
        content = []
        
        for selector in content_selectors:
            if main_content := soup.select_one(selector):
                # Extract paragraphs
                for p in main_content.find_all(['p', 'h1', 'h2', 'h3', 'pre', 'code']):
                    text = p.get_text(strip=True)
                    if text:
                        content.append(text)
                
                if content:
                    return "\n\n".join(content)
        
        # Fallback: try to find any substantial text content
        for div in soup.find_all('div'):
            text = div.get_text(strip=True)
            if len(text) > 100:  # Minimum content length
                content.append(text)
                
        return "\n\n".join(content) if content else ""

    def _extract_reading_time(self, soup: BeautifulSoup) -> int:
        """Extract reading time estimate."""
        for span in soup.find_all('span'):
            text = span.get_text(strip=True).lower()
            if 'min read' in text:
                try:
                    return int(''.join(filter(str.isdigit, text)))
                except ValueError:
                    pass
        return 0

    def _extract_claps(self, soup: BeautifulSoup) -> int:
        """Extract clap count."""
        for button in soup.find_all('button'):
            text = button.get_text(strip=True)
            if 'clap' in text.lower():
                try:
                    return int(''.join(filter(str.isdigit, text)))
                except ValueError:
                    pass
        return 0