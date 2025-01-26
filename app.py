from loguru import logger
from llmops_datacollection.domain.documents import UserDocument
from llmops_datacollection.settings import settings

def main():
    try:
        # Try to create a test user
        user = UserDocument.get_or_create(
            first_name="Test",
            last_name="User"
        )
        logger.info(f"Created/Retrieved user: {user.full_name} with ID: {user.id}")
        
        # Find the user again
        found_user = UserDocument.find(first_name="Test")
        if found_user:
            logger.info(f"Found user: {found_user.full_name}")
        else:
            logger.warning("User not found!")
            
        # Test collection existence
        if UserDocument.collection_exists():
            logger.info("Users collection exists")
        else:
            logger.warning("Users collection does not exist!")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()