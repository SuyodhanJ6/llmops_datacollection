from zenml import pipeline

from llmops_datacollection.steps.etl import crawl_links, get_or_create_user

@pipeline
def data_collection(user_full_name: str, links: list[str]) -> str:
    """Data collection pipeline.
    
    Args:
        user_full_name: Full name of the user (e.g., "John Doe")
        links: List of URLs to crawl 
    
    Returns:
        str: Last step invocation ID
    """
    user = get_or_create_user(user_full_name)
    last_step = crawl_links(user=user, links=links)

    return last_step.invocation_id