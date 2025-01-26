# import time
# from typing import Dict, List, Optional

# from bs4 import BeautifulSoup
# from bs4.element import Tag
# from loguru import logger
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.common.exceptions import TimeoutException
# from llmops_datacollection.domain.exceptions import DatabaseError

# from llmops_datacollection.domain.documents import PostDocument, UserDocument
# from llmops_datacollection.domain.exceptions import ImproperlyConfigured, CrawlerError
# from llmops_datacollection.settings import settings
# from .base import BaseSeleniumCrawler

# class LinkedInCrawler(BaseSeleniumCrawler):
#     """LinkedIn content crawler implementation."""
    
#     model = PostDocument

#     def __init__(self, scroll_limit: int = 5, timeout: int = 30) -> None:
#         """Initialize LinkedIn crawler.
        
#         Args:
#             scroll_limit: Maximum number of page scrolls
#             timeout: Maximum wait time for elements in seconds
#         """
#         super().__init__(scroll_limit)
#         self.timeout = timeout
#         self._validate_credentials()

#     def _validate_credentials(self) -> None:
#         """Validate LinkedIn credentials are configured."""
#         if not settings.LINKEDIN_EMAIL or not settings.LINKEDIN_PASSWORD:
#             raise ImproperlyConfigured(
#                 "LinkedIn credentials not configured. "
#                 "Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env"
#             )

#     def login(self) -> None:
#         """Log in to LinkedIn."""
#         try:
#             # Navigate to login page
#             self.driver.get("https://www.linkedin.com/login")
            
#             # Wait for email field
#             email_element = WebDriverWait(self.driver, self.timeout).until(
#                 EC.presence_of_element_located((By.ID, "username"))
#             )
            
#             # Enter credentials
#             email_element.send_keys(settings.LINKEDIN_EMAIL)
#             self.driver.find_element(By.ID, "password").send_keys(
#                 settings.LINKEDIN_PASSWORD
#             )
            
#             # Click login button
#             self.driver.find_element(
#                 By.CSS_SELECTOR, 
#                 ".login__form_action_container button"
#             ).click()
            
#             # Wait for login to complete
#             time.sleep(5)  # Allow for redirect and page load
            
#             logger.info("Successfully logged in to LinkedIn")
            
#         except TimeoutException:
#             raise CrawlerError("Login page elements not found")
#         except Exception as e:
#             raise CrawlerError(f"Login failed: {str(e)}")

#     def extract(self, link: str, **kwargs) -> None:
#         """Extract posts from LinkedIn profile.
        
#         Args:
#             link: LinkedIn profile URL
#             **kwargs: Additional arguments including user information
#         """
#         # Check if already crawled
#         if self.model.find(link=link):
#             logger.info(f"Posts already exist for: {link}")
#             return

#         logger.info(f"Extracting posts from: {link}")
#         user: UserDocument = kwargs.get("user")
#         if not user:
#             raise ValueError("User information required")

#         try:
#             # Login and navigate
#             self.login()
#             self.driver.get(link)
#             time.sleep(5)  # Wait for page load
            
#             # Find posts section
#             posts_button = WebDriverWait(self.driver, self.timeout).until(
#                 EC.presence_of_element_located((
#                     By.CSS_SELECTOR, 
#                     ".app-aware-link.profile-creator-shared-content-view__footer-action"
#                 ))
#             )
#             posts_button.click()
            
#             # Scroll and collect posts
#             self.scroll_page()
#             soup = BeautifulSoup(self.driver.page_source, "html.parser")
            
#             # Extract content
#             posts_data = self._extract_content(soup)
            
#             # Save posts
#             self._save_posts(posts_data, user, link)
            
#             logger.info(f"Successfully extracted {len(posts_data)} posts")
            
#         except Exception as e:
#             logger.error(f"Failed to extract posts: {str(e)}")
#             raise CrawlerError(f"Post extraction failed: {str(e)}")
#         finally:
#             self.driver.quit()

#     def _extract_content(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
#         """Extract post content from page source.
        
#         Args:
#             soup: BeautifulSoup parser for page HTML
            
#         Returns:
#             List of dictionaries containing post content
#         """
#         # Find all post containers
#         post_elements = soup.find_all(
#             "div",
#             class_="update-components-text relative update-components-update-v2__commentary"
#         )
        
#         # Find all image elements
#         image_elements = soup.find_all(
#             "button", 
#             class_="update-components-image__image-link"
#         )
        
#         # Extract images first
#         post_images = self._extract_images(image_elements)
        
#         # Combine posts and images
#         posts_data = []
#         for i, post_element in enumerate(post_elements):
#             # Extract text content
#             text_content = self._clean_post_text(
#                 post_element.get_text(strip=True)
#             )
            
#             # Create post data
#             post_data = {
#                 "text": text_content,
#                 "image": post_images.get(f"Post_{i}"),
#                 "metadata": {
#                     "index": i,
#                     "has_image": bool(post_images.get(f"Post_{i}"))
#                 }
#             }
#             posts_data.append(post_data)
            
#         return posts_data

#     def _extract_images(self, buttons: List[Tag]) -> Dict[str, str]:
#         """Extract image URLs from buttons.
        
#         Args:
#             buttons: List of button elements containing images
            
#         Returns:
#             Dictionary mapping post IDs to image URLs
#         """
#         post_images = {}
#         for i, button in enumerate(buttons):
#             if img_tag := button.find("img"):
#                 if src := img_tag.get("src"):
#                     # Clean and store image URL
#                     post_images[f"Post_{i}"] = self._clean_image_url(src)
#         return post_images

#     def _clean_post_text(self, text: str) -> str:
#         """Clean post text content.
        
#         Args:
#             text: Raw post text
            
#         Returns:
#             Cleaned text
#         """
#         # Remove excess whitespace
#         text = " ".join(text.split())
#         # Remove special characters (keep basic punctuation)
#         text = "".join(c for c in text if c.isalnum() or c in " .,!?-'\"")
#         return text.strip()

#     def _clean_image_url(self, url: str) -> str:
#         """Clean image URL.
        
#         Args:
#             url: Raw image URL
            
#         Returns:
#             Cleaned URL
#         """
#         # Remove query parameters
#         url = url.split("?")[0]
#         # Remove tracking parameters
#         url = url.split("#")[0]
#         return url

#     def _save_posts(
#         self, 
#         posts_data: List[Dict[str, str]], 
#         user: UserDocument,
#         link: str
#     ) -> None:
#         """Save posts to database.
        
#         Args:
#             posts_data: List of post content
#             user: User document
#             link: Profile URL
#         """
#         posts = [
#             PostDocument(
#                 content=post,
#                 platform="linkedin",
#                 author_id=user.id,
#                 author_full_name=user.full_name,
#                 link=link,
#                 image=post.get("image")
#             )
#             for post in posts_data
#         ]
        
#         if not self.model.bulk_insert(posts):
#             raise DatabaseError("Failed to save posts")



# In llmops_datacollection/application/crawlers/linkedin.py
import time
import os
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from bs4.element import Tag
from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    WebDriverException, 
    NoSuchElementException
)

from llmops_datacollection.domain.documents import PostDocument, UserDocument
from llmops_datacollection.domain.exceptions import ImproperlyConfigured, CrawlerError
from llmops_datacollection.settings import settings
from .base import BaseSeleniumCrawler

class LinkedInCrawler(BaseSeleniumCrawler):
    """LinkedIn content crawler implementation."""
    
    model = PostDocument

    def __init__(self, scroll_limit: int = 5, timeout: int = 60) -> None:
        """Initialize LinkedIn crawler."""
        super().__init__(scroll_limit)
        self.timeout = timeout
        self._validate_credentials()
        self.debug_dir = self._create_debug_dir()

    def _create_debug_dir(self) -> str:
        """Create a directory for debugging screenshots."""
        debug_dir = os.path.join(os.getcwd(), "linkedin_debug")
        os.makedirs(debug_dir, exist_ok=True)
        return debug_dir

    def _save_debug_screenshot(self, prefix: str = "") -> None:
        """Save a screenshot for debugging."""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{timestamp}.png"
            filepath = os.path.join(self.debug_dir, filename)
            self.driver.save_screenshot(filepath)
            logger.info(f"Debug screenshot saved: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save screenshot: {str(e)}")

    def _validate_credentials(self) -> None:
        """Validate LinkedIn credentials are configured."""
        if not settings.LINKEDIN_EMAIL or not settings.LINKEDIN_PASSWORD:
            raise ImproperlyConfigured(
                "LinkedIn credentials not configured. "
                "Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env"
            )

    def login(self) -> None:
        """Log in to LinkedIn with comprehensive error handling."""
        try:
            # Navigate to login page
            self.driver.get("https://www.linkedin.com/login")
            
            # Wait for page load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Save initial page state for debugging
            self._save_debug_screenshot("login_initial")
            
            # Find and interact with login elements
            try:
                # Wait for username input
                username_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "username"))
                )
                username_input.clear()
                username_input.send_keys(settings.LINKEDIN_EMAIL)
                
                # Wait for password input
                password_input = self.driver.find_element(By.ID, "password")
                password_input.clear()
                password_input.send_keys(settings.LINKEDIN_PASSWORD)
                
                # Find and click login button
                login_button = self.driver.find_element(
                    By.CSS_SELECTOR, 
                    ".login__form_action_container button"
                )
                login_button.click()
                
                # Wait for potential redirects or challenges
                time.sleep(5)
                
                # Save post-login page state
                self._save_debug_screenshot("login_after_submit")
                
                # Check for additional challenges (e.g., verification)
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.url_contains("feed") or 
                        EC.url_contains("checkpoint")
                    )
                except TimeoutException:
                    # Take screenshot of any potential verification page
                    self._save_debug_screenshot("login_challenge")
                    logger.warning("Possible login challenge detected")
                
                logger.info("Login attempt completed")
                
            except (NoSuchElementException, TimeoutException) as e:
                # Detailed logging for login element issues
                logger.error(f"Login element interaction failed: {str(e)}")
                self._save_debug_screenshot("login_element_error")
                raise
            
        except Exception as e:
            logger.error(f"Comprehensive login failure: {str(e)}")
            self._save_debug_screenshot("login_comprehensive_error")
            raise CrawlerError(f"Login failed: {str(e)}")

    def extract(self, link: str, **kwargs) -> None:
        """Extract posts from LinkedIn profile with enhanced error handling."""
        try:
            # Check if already crawled
            existing_posts = self.model.bulk_find(link=link)
            if existing_posts:
                logger.info(f"Posts already exist for: {link}")
                return

            logger.info(f"Extracting posts from: {link}")
            
            # Get user information
            user = kwargs.get("user")
            if not user:
                raise ValueError("User information required")

            # Login and navigate
            self.login()
            
            # Navigate to profile with retry
            for _ in range(3):
                try:
                    self.driver.get(link)
                    WebDriverWait(self.driver, self.timeout).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    break
                except TimeoutException:
                    logger.warning("Page load timeout, retrying...")
                    time.sleep(3)
            
            # Scroll and extract posts
            self._scroll_and_extract_posts(link, user)
            
        except Exception as e:
            logger.error(f"Post extraction failed: {str(e)}")
            # Take screenshot for debugging
            try:
                self.driver.save_screenshot("linkedin_extraction_error.png")
            except:
                pass
            raise CrawlerError(f"Post extraction failed: {str(e)}")
        finally:
            # Always attempt to close the driver
            try:
                self.driver.quit()
            except:
                pass

    def _scroll_and_extract_posts(self, link: str, user: UserDocument):
        """Scroll through page and extract posts."""
        # Attempt to click on posts tab
        try:
            posts_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR, 
                    ".profile-creator-shared-content-view__footer-action"
                ))
            )
            posts_button.click()
            time.sleep(3)
        except Exception as e:
            logger.warning(f"Could not click posts button: {str(e)}")

        # Scroll multiple times
        for _ in range(self.scroll_limit):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        # Parse page
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        
        # Find post elements
        post_elements = soup.find_all(
            "div", 
            class_="update-components-text relative update-components-update-v2__commentary"
        )
        
        # Limit posts to prevent overwhelming storage
        post_elements = post_elements[:20]  # Limit to 20 most recent posts
        
        posts = []
        for i, post_element in enumerate(post_elements):
            try:
                post_text = post_element.get_text(strip=True)
                
                # Create post document
                post = self.model(
                    content={
                        "text": post_text,
                        "index": i
                    },
                    platform="linkedin",
                    author_id=user.id,  # This is now a UUID4
                    author_full_name=user.full_name,
                    link=link
                )
                posts.append(post)
            except Exception as e:
                logger.warning(f"Failed to process post {i}: {str(e)}")
        
        # Bulk insert posts
        if posts:
            self.model.bulk_insert(posts)
            logger.info(f"Saved {len(posts)} posts from LinkedIn profile")
        else:
            logger.warning("No posts found to save")