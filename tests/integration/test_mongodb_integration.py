import pytest
from pymongo.errors import OperationFailure

from llmops_datacollection.domain.documents import UserDocument
from llmops_datacollection.domain.exceptions import DatabaseError

@pytest.mark.integration
def test_database_connection(mongo_client):
    """Test MongoDB connection."""
    try:
        # Test connection
        mongo_client.admin.command('ping')
    except OperationFailure as e:
        pytest.fail(f"Database connection failed: {str(e)}")

@pytest.mark.integration
def test_full_user_workflow():
    """Test complete user document workflow."""
    # Create user
    user = UserDocument(
        first_name="Integration",
        last_name="Test"
    )
    
    # Save
    saved_user = user.save()
    assert saved_user is not None
    
    # Find
    found_user = UserDocument.find(first_name="Integration")
    assert found_user is not None
    assert found_user.id == user.id
    
    # Bulk operations
    more_users = [
        UserDocument(first_name=f"Bulk{i}", last_name="Test")
        for i in range(3)
    ]
    assert UserDocument.bulk_insert(more_users) is True
    
    # Find all test users
    test_users = UserDocument.bulk_find(last_name="Test")
    assert len(test_users) == 4  # Original + 3 bulk inserted

@pytest.mark.integration
def test_collection_operations():
    """Test collection management operations."""
    assert UserDocument.collection_exists() is True
    
    # Test get_or_create with new collection
    class TestDocument(UserDocument):
        _collection = "test_collection"
    
    test_doc = TestDocument(
        first_name="Test",
        last_name="Collection"
    )
    saved_doc = test_doc.save()
    assert saved_doc is not None
    assert TestDocument.collection_exists() is True