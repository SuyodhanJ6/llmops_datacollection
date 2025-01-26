import pytest
from pymongo import MongoClient

from llmops_datacollection.domain.documents import UserDocument
from llmops_datacollection.infrastructure.db.mongo import MongoDBConnector
from llmops_datacollection.settings import settings

@pytest.fixture(scope="session")
def mongo_client():
    """Create MongoDB test client."""
    client = MongoClient(settings.DATABASE_HOST)
    yield client
    client.close()

@pytest.fixture(scope="session")
def test_db(mongo_client):
    """Create test database."""
    db_name = f"{settings.DATABASE_NAME}_test"
    db = mongo_client[db_name]
    yield db
    mongo_client.drop_database(db_name)

@pytest.fixture
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