# tests/conftest.py

import pytest
from pymongo import MongoClient
from unittest.mock import Mock, patch

from llmops_datacollection.domain.documents import UserDocument
from llmops_datacollection.infrastructure.db.mongo import MongoDBConnector
from llmops_datacollection.settings import settings

@pytest.fixture(scope="session")
def mongo_client():
    """Create MongoDB test client."""
    client = MongoClient(settings.MONGODB_URI)
    yield client
    client.close()

@pytest.fixture(scope="function")
def test_db(mongo_client):
    """Create test database."""
    db = mongo_client[settings.DATABASE_NAME]
    
    # Store original collection names to clean up only test collections
    original_collections = set(db.list_collection_names())
    
    yield db
    
    # Cleanup only test collections
    current_collections = set(db.list_collection_names())
    test_collections = current_collections - original_collections
    for collection in test_collections:
        db.drop_collection(collection)

@pytest.fixture(scope="function")
def test_user():
    """Create test user."""
    user = UserDocument(
        first_name="Test",
        last_name="User"
    )
    return user

@pytest.fixture(autouse=True)
def mock_mongodb_connection(monkeypatch, test_db):
    """Mock MongoDB connection."""
    def mock_get_collection(self, name):
        # Append _test to collection names for isolation
        test_name = f"{name}_test"
        return test_db[test_name]
        
    monkeypatch.setattr(
        MongoDBConnector,
        "get_collection",
        mock_get_collection
    )

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "cli: marks tests as CLI tests"
    )