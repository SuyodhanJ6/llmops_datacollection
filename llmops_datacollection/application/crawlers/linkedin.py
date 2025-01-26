import time
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from bs4.element import Tag
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from llmops_datacollection.domain.exceptions import DatabaseError

from llmops_datacollection.domain.documents import PostDocument, UserDocument
from llmops_datacollection.domain.exceptions import ImproperlyConfigured, CrawlerError
from llmops_datacollection.settings import settings
from .base import BaseSeleniumCrawler

class LinkedInCrawler(BaseSeleniumCrawler):
    """LinkedIn content crawler implementation."""
    
    model = PostDocument

    def __init__(self, scroll_limit: int = 5, timeout: int = 30) -> None:
        """Initialize LinkedIn crawler.
        
        Args:
            scroll_limit: Maximum number of page scrolls
            timeout: Maximum wait time for elements in seconds
        """
        super().__init__(scroll_limit)
        self.timeout = timeout
        self._validate_credentials()

    def _validate_credentials(self) -> None:
        """Validate LinkedIn credentials are configured."""
        if not settings.LINKEDIN_EMAIL or not settings.LINKEDIN_PASSWORD:
            raise ImproperlyConfigured(
                "LinkedIn credentials not configured. "
                "Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env"
            )

    def login(self) -> None:
        """Log in to LinkedIn."""
        try:
            # Navigate to login page
            self.driver.get("https://www.linkedin.com/login")
            
            # Wait for email field
            email_element = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            
            # Enter credentials
            email_element.send_keys(settings.LINKEDIN_EMAIL)
            self.driver.find_element(By.ID, "password").send_keys(
                settings.LINKEDIN_PASSWORD
            )
            
            # Click login button
            self.driver.find_element(
                By.CSS_SELECTOR, 
                ".login__form_action_container button"
            ).click()
            
            # Wait for login to complete
            time.sleep(5)  # Allow for redirect and page load
            
            logger.info("Successfully logged in to LinkedIn")
            
        except TimeoutException:
            raise CrawlerError("Login page elements not found")
        except Exception as e:
            raise CrawlerError(f"Login failed: {str(e)}")

    def extract(self, link: str, **kwargs) -> None:
        """Extract posts from LinkedIn profile.
        
        Args:
            link: LinkedIn profile URL
            **kwargs: Additional arguments including user information
        """
        # Check if already crawled
        if self.model.find(link=link):
            logger.info(f"Posts already exist for: {link}")
            return

        logger.info(f"Extracting posts from: {link}")
        user: UserDocument = kwargs.get("user")
        if not user:
            raise ValueError("User information required")

        try:
            # Login and navigate
            self.login()
            self.driver.get(link)
            time.sleep(5)  # Wait for page load
            
            # Find posts section
            posts_button = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    ".app-aware-link.profile-creator-shared-content-view__footer-action"
                ))
            )
            posts_button.click()
            
            # Scroll and collect posts
            self.scroll_page()
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            
            # Extract content
            posts_data = self._extract_content(soup)
            
            # Save posts
            self._save_posts(posts_data, user, link)
            
            logger.info(f"Successfully extracted {len(posts_data)} posts")
            
        except Exception as e:
            logger.error(f"Failed to extract posts: {str(e)}")
            raise CrawlerError(f"Post extraction failed: {str(e)}")
        finally:
            self.driver.quit()

    def _extract_content(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract post content from page source.
        
        Args:
            soup: BeautifulSoup parser for page HTML
            
        Returns:
            List of dictionaries containing post content
        """
        # Find all post containers
        post_elements = soup.find_all(
            "div",
            class_="update-components-text relative update-components-update-v2__commentary"
        )
        
        # Find all image elements
        image_elements = soup.find_all(
            "button", 
            class_="update-components-image__image-link"
        )
        
        # Extract images first
        post_images = self._extract_images(image_elements)
        
        # Combine posts and images
        posts_data = []
        for i, post_element in enumerate(post_elements):
            # Extract text content
            text_content = self._clean_post_text(
                post_element.get_text(strip=True)
            )
            
            # Create post data
            post_data = {
                "text": text_content,
                "image": post_images.get(f"Post_{i}"),
                "metadata": {
                    "index": i,
                    "has_image": bool(post_images.get(f"Post_{i}"))
                }
            }
            posts_data.append(post_data)
            
        return posts_data

    def _extract_images(self, buttons: List[Tag]) -> Dict[str, str]:
        """Extract image URLs from buttons.
        
        Args:
            buttons: List of button elements containing images
            
        Returns:
            Dictionary mapping post IDs to image URLs
        """
        post_images = {}
        for i, button in enumerate(buttons):
            if img_tag := button.find("img"):
                if src := img_tag.get("src"):
                    # Clean and store image URL
                    post_images[f"Post_{i}"] = self._clean_image_url(src)
        return post_images

    def _clean_post_text(self, text: str) -> str:
        """Clean post text content.
        
        Args:
            text: Raw post text
            
        Returns:
            Cleaned text
        """
        # Remove excess whitespace
        text = " ".join(text.split())
        # Remove special characters (keep basic punctuation)
        text = "".join(c for c in text if c.isalnum() or c in " .,!?-'\"")
        return text.strip()

    def _clean_image_url(self, url: str) -> str:
        """Clean image URL.
        
        Args:
            url: Raw image URL
            
        Returns:
            Cleaned URL
        """
        # Remove query parameters
        url = url.split("?")[0]
        # Remove tracking parameters
        url = url.split("#")[0]
        return url

    def _save_posts(
        self, 
        posts_data: List[Dict[str, str]], 
        user: UserDocument,
        link: str
    ) -> None:
        """Save posts to database.
        
        Args:
            posts_data: List of post content
            user: User document
            link: Profile URL
        """
        posts = [
            PostDocument(
                content=post,
                platform="linkedin",
                author_id=user.id,
                author_full_name=user.full_name,
                link=link,
                image=post.get("image")
            )
            for post in posts_data
        ]
        
        if not self.model.bulk_insert(posts):
            raise DatabaseError("Failed to save posts")