import time
from abc import ABC, abstractmethod
from tempfile import mkdtemp

import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from llmops_datacollection.domain.base import NoSQLBaseDocument

# Install chromedriver if needed
chromedriver_autoinstaller.install()

class BaseCrawler(ABC):
    """Base crawler class."""
    
    model: type[NoSQLBaseDocument]

    @abstractmethod
    def extract(self, link: str, **kwargs) -> None:
        """Extract data from the given link."""
        pass

class BaseSeleniumCrawler(BaseCrawler, ABC):
    """Base Selenium-based crawler."""
    
    def __init__(self, scroll_limit: int = 5) -> None:
        self.scroll_limit = scroll_limit
        self.driver = self._setup_driver()

    def _setup_driver(self) -> webdriver.Chrome:
        """Set up Chrome WebDriver."""
        options = webdriver.ChromeOptions()
        
        # Configure Chrome options
        options.add_argument("--no-sandbox")
        options.add_argument("--headless=new")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-extensions")
        options.add_argument("--ignore-certificate-errors")
        
        # Use temporary directories
        options.add_argument(f"--user-data-dir={mkdtemp()}")
        options.add_argument(f"--data-path={mkdtemp()}")
        options.add_argument(f"--disk-cache-dir={mkdtemp()}")
        
        return webdriver.Chrome(options=options)

    def scroll_page(self) -> None:
        """Scroll through the page."""
        current_scroll = 0
        last_height = self.driver.execute_script(
            "return document.body.scrollHeight"
        )
        
        while True:
            # Scroll down
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(2)
            
            # Calculate new scroll height
            new_height = self.driver.execute_script(
                "return document.body.scrollHeight"
            )
            
            # Check if we've reached the bottom or scroll limit
            if (new_height == last_height or 
                (self.scroll_limit and current_scroll >= self.scroll_limit)):
                break
                
            last_height = new_height
            current_scroll += 1