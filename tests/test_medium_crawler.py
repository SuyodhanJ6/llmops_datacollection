# test_medium_crawler.py

import click
from loguru import logger

from llmops_datacollection.application.crawlers.medium import MediumCrawler
from llmops_datacollection.domain.documents import UserDocument, ArticleDocument

@click.group()
def cli():
    """Medium Crawler Testing CLI"""
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
    help="Medium article URL to crawl"
)
def crawl_medium(user_name: str, url: str):
    """Crawl specified Medium article."""
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
        
        # Initialize Medium crawler
        crawler = MediumCrawler()
        
        # Check if article already exists
        if ArticleDocument.find(link=url):
            logger.info(f"Article already exists: {url}")
            return
        
        # Crawl article URL
        logger.info(f"Crawling Medium article: {url}")
        crawler.extract(url, user=user)
        
        # Verify article was saved
        article = ArticleDocument.find(link=url)
        if article:
            logger.info(f"Successfully crawled article: {article.content.get('title', 'Untitled')}")
            logger.info("Article metadata:")
            logger.info(f"- Reading time: {article.content.get('metadata', {}).get('reading_time', 'Unknown')} minutes")
            logger.info(f"- Claps: {article.content.get('metadata', {}).get('claps', 'Unknown')}")
        else:
            logger.warning("Article was not saved successfully")
        
        logger.info("Medium crawling completed successfully")
        
    except Exception as e:
        logger.error(f"Medium crawling failed: {str(e)}")
        raise click.ClickException(str(e))

@cli.command()
@click.option(
    "--user-name",
    required=True,
    help="Full name of the user to list articles for"
)
def list_articles(user_name: str):
    """List all crawled Medium articles for a user."""
    try:
        # Split user name
        name_parts = user_name.split()
        first_name = " ".join(name_parts[:-1])
        last_name = name_parts[-1]
        
        # Find user
        user = UserDocument.find(
            first_name=first_name,
            last_name=last_name
        )
        
        if not user:
            raise click.ClickException(f"User not found: {user_name}")
            
        # Get user's articles
        articles = ArticleDocument.bulk_find(author_id=user.id)
        
        if not articles:
            logger.info(f"No articles found for user: {user.full_name}")
            return
            
        # Display articles
        logger.info(f"\nArticles for {user.full_name}:")
        for i, article in enumerate(articles, 1):
            logger.info(f"\n{i}. {article.content.get('title', 'Untitled')}")
            logger.info(f"   URL: {article.link}")
            logger.info(f"   Platform: {article.platform}")
            if 'reading_time' in article.content.get('metadata', {}):
                logger.info(f"   Reading time: {article.content['metadata']['reading_time']} minutes")
            
        logger.info(f"\nTotal articles found: {len(articles)}")
        
    except Exception as e:
        logger.error(f"Failed to list articles: {str(e)}")
        raise click.ClickException(str(e))

if __name__ == "__main__":
    cli()