# from typing import Any, Optional
# from loguru import logger
# from pymongo import MongoClient
# from pymongo.collection import Collection
# from pymongo.database import Database
# from pymongo.errors import ConnectionFailure

# from llmops_datacollection.domain.exceptions import DatabaseError
# from llmops_datacollection.settings import settings

# class MongoDBConnector:
#     """MongoDB connection manager."""
    
#     _instance: Optional['MongoDBConnector'] = None
#     _client: Optional[MongoClient] = None
#     _db: Optional[Database] = None
    
#     def __new__(cls) -> 'MongoDBConnector':
#         if cls._instance is None:
#             cls._instance = super().__new__(cls)
#         return cls._instance
    
#     def __init__(self) -> None:
#         if self._client is None:
#             try:
#                 self._client = MongoClient(settings.MONGODB_URI)
#                 self._db = self._client[settings.DATABASE_NAME]
#                 # Test connection
#                 self._client.admin.command('ping')
#                 logger.info(
#                     f"Connected to MongoDB at {settings.MONGODB_URI}"
#                     f" using database {settings.DATABASE_NAME}"
#                 )
#             except ConnectionFailure as e:
#                 raise DatabaseError(f"Failed to connect to MongoDB: {str(e)}") from e

#     @property
#     def client(self) -> MongoClient:
#         if self._client is None:
#             raise DatabaseError("MongoDB client not initialized")
#         return self._client
    
#     @property
#     def db(self) -> Database:
#         if self._db is None:
#             raise DatabaseError("Database not initialized")
#         return self._db
    
#     def get_collection(self, name: str) -> Collection:
#         """Get collection by name."""
#         return self.db[name]

#     def create_collection(self, name: str, **kwargs: Any) -> Collection:
#         """Create new collection."""
#         try:
#             return self.db.create_collection(name, **kwargs)
#         except Exception as e:
#             raise DatabaseError(
#                 f"Failed to create collection {name}: {str(e)}"
#             ) from e
    
#     def list_collection_names(self) -> list[str]:
#         """Get list of collection names."""
#         return self.db.list_collection_names()
    
#     def drop_collection(self, name: str) -> None:
#         """Drop collection by name."""
#         try:
#             self.db.drop_collection(name)
#         except Exception as e:
#             raise DatabaseError(
#                 f"Failed to drop collection {name}: {str(e)}"
#             ) from e
    
#     def __del__(self) -> None:
#         """Close MongoDB connection on cleanup."""
#         if self._client is not None:
#             self._client.close()
#             logger.info("Closed MongoDB connection")

# # Global connection instance
# connection = MongoDBConnector()


# llmops_datacollection/infrastructure/db/mongo.py
from typing import Any, Optional
from loguru import logger
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure
from bson.binary import Binary
import uuid

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
                # Configure UUID representation
                client_options = {
                    'uuidRepresentation': 'standard'  # This helps with UUID encoding
                }
                
                self._client = MongoClient(
                    settings.MONGODB_URI, 
                    **client_options
                )
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
        """Get the MongoDB client."""
        if self._client is None:
            raise DatabaseError("MongoDB client not initialized")
        return self._client

    @property
    def db(self) -> Database:
        """Get the MongoDB database."""
        if self._db is None:
            raise DatabaseError("Database not initialized")
        return self._db

    def convert_uuid_to_binary(self, value):
        """Convert UUID to BSON Binary."""
        if isinstance(value, uuid.UUID):
            return Binary(value.bytes, subtype=4)
        return value

    def prepare_document_for_insertion(self, document: dict) -> dict:
        """Prepare document for MongoDB insertion by converting UUIDs."""
        converted_doc = {}
        for key, value in document.items():
            if isinstance(value, dict):
                converted_doc[key] = self.prepare_document_for_insertion(value)
            elif isinstance(value, list):
                converted_doc[key] = [
                    self.prepare_document_for_insertion(item) if isinstance(item, dict) else self.convert_uuid_to_binary(item)
                    for item in value
                ]
            else:
                converted_doc[key] = self.convert_uuid_to_binary(value)
        return converted_doc

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
    
    def insert_one(self, collection: Collection, document: dict) -> Any:
        """Insert a single document with UUID conversion."""
        prepared_doc = self.prepare_document_for_insertion(document)
        return collection.insert_one(prepared_doc)
    
    def insert_many(self, collection: Collection, documents: list[dict]) -> Any:
        """Insert multiple documents with UUID conversion."""
        prepared_docs = [self.prepare_document_for_insertion(doc) for doc in documents]
        return collection.insert_many(prepared_docs)

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