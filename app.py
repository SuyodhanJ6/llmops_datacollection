import click
from loguru import logger

from llmops_datacollection.application.crawlers.linkedin import LinkedInCrawler 
from llmops_datacollection.domain.documents import UserDocument

@click.group()
def cli():
    """LLMOps Data Collection CLI"""
    pass

@cli.command()
@click.option(
    "--user-name",
    required=True,
    help="Full name of the user (e.g., 'John Doe')"
)
@click.option(
    "--url",
    required=True,
    help="LinkedIn profile URL to crawl"
)
def crawl_linkedin(user_name: str, url: str):
    """Crawl specified LinkedIn profile for content."""
    try:
        # Split user name
        name_parts = user_name.split()
        if len(name_parts) < 2:
            raise ValueError("User name must include first and last name")
            
        first_name = " ".join(name_parts[:-1])
        last_name = name_parts[-1]
        
        # Get or create user
        user = UserDocument.get_or_create(
            first_name=first_name,
            last_name=last_name
        )
        logger.info(f"User: {user.full_name}")
        
        # Initialize LinkedIn crawler
        crawler = LinkedInCrawler()
        
        # Crawl profile URL
        logger.info(f"Crawling LinkedIn profile: {url}")
        crawler.extract(url, user=user)
        
        logger.info("LinkedIn crawling completed successfully")
        
    except Exception as e:
        logger.error(f"LinkedIn crawling failed: {str(e)}")
        raise click.ClickException(str(e))

if __name__ == "__main__":
    cli()