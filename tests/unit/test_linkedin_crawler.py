# tests/unit/test_linkedin_crawler.py

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from llmops_datacollection.application.crawlers.linkedin import LinkedInCrawler
from llmops_datacollection.domain.documents import UserDocument, PostDocument
from llmops_datacollection.domain.exceptions import CrawlerError

@pytest.fixture
def mock_webdriver():
    """Mock Selenium WebDriver."""
    with patch('selenium.webdriver.Chrome') as mock_chrome:
        mock_driver = Mock()
        mock_driver.page_source = ""
        mock_chrome.return_value = mock_driver
        yield mock_driver

@pytest.fixture
def linkedin_crawler(mock_webdriver):
    """Initialize LinkedIn crawler with mocked driver."""
    with patch('llmops_datacollection.application.crawlers.linkedin.LinkedInCrawler._setup_driver') as mock_setup:
        mock_setup.return_value = mock_webdriver
        crawler = LinkedInCrawler()
        crawler.driver = mock_webdriver
        yield crawler

def test_initialization(linkedin_crawler):
    """Test crawler initialization."""
    assert linkedin_crawler.scroll_limit == 5
    assert linkedin_crawler.timeout == 60
    assert hasattr(linkedin_crawler, 'driver')

def test_scroll_page(linkedin_crawler):
    """Test page scrolling."""
    # Mock scroll heights
    linkedin_crawler.driver.execute_script.side_effect = [
        1000,  # Initial height
        2000,  # New height
        2000   # Same height (stop condition)
    ]
    
    linkedin_crawler.scroll_page()
    assert linkedin_crawler.driver.execute_script.call_count >= 2

@patch('time.sleep')  # Mock sleep to speed up test
def test_login_process(mock_sleep, linkedin_crawler):
    """Test login functionality."""
    # Mock find_element returns
    mock_username = Mock()
    mock_password = Mock()
    linkedin_crawler.driver.find_element.side_effect = [mock_username, mock_password]
    
    with patch.dict(os.environ, {
        'LINKEDIN_EMAIL': 'test@example.com',
        'LINKEDIN_PASSWORD': 'test123'
    }):
        linkedin_crawler.login()
    
    # Verify login actions
    linkedin_crawler.driver.get.assert_called_with('https://www.linkedin.com/login')
    mock_username.send_keys.assert_called_once()
    mock_password.send_keys.assert_called_once()

def test_post_extraction(linkedin_crawler, test_user):
    """Test post content extraction."""
    # Mock page source with test posts
    linkedin_crawler.driver.page_source = """
    <div class="update-components-text relative update-components-update-v2__commentary">
        <div>Test post content</div>
    </div>
    """
    
    with patch.object(PostDocument, 'bulk_insert') as mock_insert:
        linkedin_crawler._scroll_and_extract_posts(
            "https://linkedin.com/in/testuser",
            test_user
        )
        
        # Verify post extraction
        mock_insert.assert_called_once()
        posts = mock_insert.call_args[0][0]
        assert len(posts) > 0
        assert all(isinstance(p, PostDocument) for p in posts)

def test_error_handling(linkedin_crawler, test_user):
    """Test error handling."""
    linkedin_crawler.driver.get.side_effect = Exception("Test error")
    
    with pytest.raises(CrawlerError):
        linkedin_crawler.extract(
            "https://linkedin.com/in/testuser",
            user=test_user
        )

def test_login_timeout(linkedin_crawler):
    """Test login timeout handling."""
    linkedin_crawler.driver.find_element.side_effect = TimeoutException()
    
    with pytest.raises(CrawlerError):
        linkedin_crawler.login()