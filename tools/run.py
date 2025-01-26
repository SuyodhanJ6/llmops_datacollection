import click
from loguru import logger

from llmops_datacollection.application.crawlers.dispatcher import CrawlerDispatcher
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
    "--urls",
    required=True,
    multiple=True,
    help="URLs to crawl (can be specified multiple times)"
)
def crawl(user_name: str, urls: tuple[str]):
    """Crawl specified URLs for content."""
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
        
        # Initialize dispatcher
        dispatcher = CrawlerDispatcher.build()
        
        # Crawl URLs
        logger.info(f"Crawling {len(urls)} URLs")
        dispatcher.crawl_urls(list(urls), user=user)
        
        logger.info("Crawling completed successfully")
        
    except Exception as e:
        logger.error(f"Crawling failed: {str(e)}")
        raise click.ClickException(str(e))

@cli.command()
@click.option(
    "--user-name",
    required=True,
    help="Full name of the user to list content for"
)
def list_content(user_name: str):
    """List crawled content for a user."""
    try:
        # Get user
        name_parts = user_name.split()
        first_name = " ".join(name_parts[:-1])
        last_name = name_parts[-1]
        
        user = UserDocument.find(
            first_name=first_name,
            last_name=last_name
        )
        
        if not user:
            raise click.ClickException(f"User not found: {user_name}")
            
        # Get content counts
        from llmops_datacollection.domain.documents import (
            ArticleDocument, PostDocument, RepositoryDocument
        )
        
        articles = ArticleDocument.bulk_find(author_id=user.id)
        posts = PostDocument.bulk_find(author_id=user.id)
        repos = RepositoryDocument.bulk_find(author_id=user.id)
        
        # Display results
        click.echo(f"\nContent for {user.full_name}:")
        click.echo(f"Articles: {len(articles)}")
        click.echo(f"Posts: {len(posts)}")
        click.echo(f"Repositories: {len(repos)}")
        
    except Exception as e:
        logger.error(f"Failed to list content: {str(e)}")
        raise click.ClickException(str(e))

if __name__ == "__main__":
    cli()