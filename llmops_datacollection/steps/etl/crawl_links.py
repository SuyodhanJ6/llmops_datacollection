from loguru import logger
from tqdm import tqdm
from typing_extensions import Annotated
from zenml import get_step_context, step

from llmops_datacollection.application.crawlers.dispatcher import CrawlerDispatcher
from llmops_datacollection.domain.documents import UserDocument

@step
def crawl_links(user: Annotated[UserDocument, "user"], links: list[str]) -> Annotated[list[str], "crawled_links"]:
    """Crawl provided links to extract content.
    
    Args:
        user: User document
        links: List of URLs to crawl
        
    Returns:
        list[str]: List of crawled links
    """
    dispatcher = CrawlerDispatcher.build()
    
    logger.info(f"Starting to crawl {len(links)} link(s).")

    metadata = {}
    successful_crawls = 0
    for link in tqdm(links):
        try:
            # Get appropriate crawler for link type
            crawler = dispatcher.get_crawler(link)
            
            # Extract content from link
            crawler.extract(link=link, user=user)
            successful_crawls += 1
            
            # Update metadata
            platform = crawler.model._collection
            if platform not in metadata:
                metadata[platform] = {
                    "successful": 0,
                    "total": 0
                }
            metadata[platform]["successful"] += 1
            metadata[platform]["total"] += 1
            
        except Exception as e:
            logger.error(f"Failed to crawl {link}: {str(e)}")
            
            # Update metadata for failed crawl
            platform = "unknown"
            if platform not in metadata:
                metadata[platform] = {
                    "successful": 0, 
                    "total": 0
                }
            metadata[platform]["total"] += 1

    step_context = get_step_context()
    step_context.add_output_metadata(output_name="crawled_links", metadata=metadata)

    logger.info(f"Successfully crawled {successful_crawls} / {len(links)} links.")

    return links