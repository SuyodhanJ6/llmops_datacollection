from typing import Any, Optional
from loguru import logger
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure

from llmops_datacollection.domain.exceptions import DatabaseError
from llmops_datacollection.settings import settings

class MongoDBConnector:
    """MongoDB connection manager."""
    
    _instance: Optional['MongoDBConnector'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    
    def __new__(cls) -> 'MongoDBConnector':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if self._client is None:
            try:
                self._client = MongoClient(settings.MONGODB_URI)
                self._db = self._client[settings.DATABASE_NAME]
                # Test connection
                self._client.admin.command('ping')
                logger.info(
                    f"Connected to MongoDB at {settings.MONGODB_URI}"
                    f" using database {settings.DATABASE_NAME}"
                )
            except ConnectionFailure as e:
                raise DatabaseError(f"Failed to connect to MongoDB: {str(e)}") from e

    @property
    def client(self) -> MongoClient:
        if self._client is None:
            raise DatabaseError("MongoDB client not initialized")
        return self._client
    
    @property
    def db(self) -> Database:
        if self._db is None:
            raise DatabaseError("Database not initialized")
        return self._db
    
    def get_collection(self, name: str) -> Collection:
        """Get collection by name."""
        return self.db[name]

    def create_collection(self, name: str, **kwargs: Any) -> Collection:
        """Create new collection."""
        try:
            return self.db.create_collection(name, **kwargs)
        except Exception as e:
            raise DatabaseError(
                f"Failed to create collection {name}: {str(e)}"
            ) from e
    
    def list_collection_names(self) -> list[str]:
        """Get list of collection names."""
        return self.db.list_collection_names()
    
    def drop_collection(self, name: str) -> None:
        """Drop collection by name."""
        try:
            self.db.drop_collection(name)
        except Exception as e:
            raise DatabaseError(
                f"Failed to drop collection {name}: {str(e)}"
            ) from e
    
    def __del__(self) -> None:
        """Close MongoDB connection on cleanup."""
        if self._client is not None:
            self._client.close()
            logger.info("Closed MongoDB connection")

# Global connection instance
connection = MongoDBConnector()