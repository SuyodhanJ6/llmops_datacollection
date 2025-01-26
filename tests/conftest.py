import pytest
from pymongo import MongoClient
from unittest.mock import Mock, patch

from llmops_datacollection.domain.documents import UserDocument
from llmops_datacollection.infrastructure.db.mongo import MongoDBConnector
from llmops_datacollection.settings import settings

@pytest.fixture(scope="session")
def mongo_client():
    """Create MongoDB test client."""
    # Use test database name
    test_uri = settings.MONGODB_URI
    client = MongoClient(test_uri)
    yield client
    client.close()

@pytest.fixture(scope="function")
def test_db(mongo_client):
    """Create test database."""
    db_name = f"{settings.DATABASE_NAME}_test"
    db = mongo_client[db_name]
    yield db
    # Cleanup after test
    mongo_client.drop_database(db_name)

@pytest.fixture(scope="function")
def test_user():
    """Create test user."""
    user = UserDocument(
        first_name="Test",
        last_name="User"
    )
    user.save()
    yield user

@pytest.fixture(autouse=True)
def mock_mongodb_connection(monkeypatch, test_db):
    """Mock MongoDB connection to use test database."""
    def mock_get_collection(self, name):
        return test_db[name]
        
    monkeypatch.setattr(
        MongoDBConnector,
        "get_collection",
        mock_get_collection
    )