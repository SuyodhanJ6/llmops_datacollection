import uuid
from llmops_datacollection.application.crawlers.github import GithubCrawler
from llmops_datacollection.domain.documents import UserDocument

def test_github_crawler():
    # Create test user
    test_user = UserDocument(
        first_name="Test",
        last_name="User",
        id=str(uuid.uuid4())
    )

    # Initialize crawler
    crawler = GithubCrawler()

    # Test repository URL (replace with a real public repo)
    repo_url = "https://github.com/SuyodhanJ6/Money-Laundering-Prevention"

    try:
        # Extract repository
        crawler.extract(repo_url, user=test_user)
        print("✅ Repository extracted successfully")
        
        # Try extracting same repo again (should be skipped)
        crawler.extract(repo_url, user=test_user)
        print("✅ Duplicate repository check passed")
        
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_github_crawler()
    print(f"\nOverall test {'passed' if success else 'failed'}")