import pytest
from unittest.mock import Mock, patch

from llmops_datacollection.application.crawlers.dispatcher import CrawlerDispatcher
from llmops_datacollection.application.crawlers.linkedin import LinkedInCrawler
from llmops_datacollection.application.crawlers.medium import MediumCrawler
from llmops_datacollection.application.crawlers.github import GithubCrawler
from llmops_datacollection.domain.documents import UserDocument

@pytest.fixture
def user():
    """Create test user."""
    return UserDocument(
        first_name="Test",
        last_name="User"
    )

@pytest.fixture
def dispatcher():
    """Create crawler dispatcher."""
    return CrawlerDispatcher.build()

def test_dispatcher_gets_correct_crawler(dispatcher):
    """Test that dispatcher returns correct crawler for URL."""
    linkedin_url = "https://linkedin.com/in/testuser"
    medium_url = "https://medium.com/@testuser"
    github_url = "https://github.com/testuser/repo"

    assert isinstance(dispatcher.get_crawler(linkedin_url), LinkedInCrawler)
    assert isinstance(dispatcher.get_crawler(medium_url), MediumCrawler)
    assert isinstance(dispatcher.get_crawler(github_url), GithubCrawler)

def test_dispatcher_invalid_url(dispatcher):
    """Test that dispatcher raises error for invalid URL."""
    with pytest.raises(ValueError):
        dispatcher.get_crawler("https://invalid.com")

@patch('selenium.webdriver.Chrome')
def test_linkedin_crawler(mock_chrome, user):
    """Test LinkedIn crawler."""
    mock_driver = Mock()
    mock_chrome.return_value = mock_driver
    
    # Mock page source
    mock_driver.page_source = """
        <div class="update-components-text relative update-components-update-v2__commentary">
            Test post content
        </div>
    """
    
    crawler = LinkedInCrawler()
    with patch.object(crawler.model, 'bulk_insert') as mock_insert:
        crawler.extract("https://linkedin.com/in/testuser", user=user)
        mock_insert.assert_called_once()

@patch('subprocess.run')
def test_github_crawler(mock_run, user):
    """Test GitHub crawler."""
    mock_run.return_value = Mock(returncode=0)
    
    crawler = GithubCrawler()
    with patch.object(crawler.model, 'save') as mock_save:
        crawler.extract("https://github.com/testuser/repo", user=user)
        mock_save.assert_called_once()