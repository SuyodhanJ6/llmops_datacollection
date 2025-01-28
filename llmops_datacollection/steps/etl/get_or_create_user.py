from loguru import logger
from typing_extensions import Annotated 
from zenml import get_step_context, step

from llmops_datacollection.application import utils
from llmops_datacollection.domain.documents import UserDocument

@step
def get_or_create_user(user_full_name: str) -> Annotated[UserDocument, "user"]:
    """Get or create user from full name.
    
    Args:
        user_full_name: Full name of user (e.g., "John Doe")
    
    Returns:
        UserDocument: Retrieved or created user
    """
    logger.info(f"Getting or creating user: {user_full_name}")

    first_name, last_name = utils.text.split_full_name(user_full_name)

    user = UserDocument.get_or_create(first_name=first_name, last_name=last_name)

    step_context = get_step_context()
    step_context.add_output_metadata(output_name="user", metadata=_get_metadata(user_full_name, user))

    return user

def _get_metadata(user_full_name: str, user: UserDocument) -> dict:
    """Get step metadata.
    
    Args:
        user_full_name: Full name used to find/create user
        user: User document
        
    Returns:
        dict: Step metadata
    """
    return {
        "query": {
            "user_full_name": user_full_name,
        },
        "retrieved": {
            "user_id": str(user.id),
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
    }