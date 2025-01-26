import uuid
from abc import ABC
from typing import Any, ClassVar, Dict, Generic, Type, TypeVar

from loguru import logger
from pydantic import BaseModel, Field, ConfigDict
from pydantic.types import UUID4
from pymongo import errors

from llmops_datacollection.domain.exceptions import DatabaseError
from llmops_datacollection.infrastructure.db.mongo import connection

T = TypeVar("T", bound="NoSQLBaseDocument")

class NoSQLBaseDocument(BaseModel, ABC):
    """Base document model with MongoDB integration."""
    
    id: UUID4 = Field(default_factory=uuid.uuid4, alias="_id")
    _collection: ClassVar[str | None] = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        extra='allow',
        from_attributes=True,
        json_encoders={
            UUID4: str,  # Ensure UUID is converted to string for JSON
            uuid.UUID: str  # Additional UUID conversion
        }
    )

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, self.__class__):
            return False
        return self.id == value.id

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def collection_exists(cls) -> bool:
        """Check if collection exists in MongoDB."""
        try:
            collection_names = connection.list_collection_names()
            return cls._collection in collection_names
        except errors.OperationFailure as e:
            logger.error(f"Failed to check collection existence: {str(e)}")
            raise DatabaseError(f"Failed to check collection: {str(e)}")

    @classmethod
    def get_collection_name(cls) -> str:
        """Get or create MongoDB collection name."""
        if cls._collection is None:
            raise ValueError(f"Collection name not set for {cls.__name__}")
            
        try:
            # Get existing collection
            connection.get_collection(cls._collection)
        except errors.OperationFailure:
            logger.info(f"Collection {cls._collection} does not exist, creating...")
            try:
                # Create new collection 
                connection.create_collection(cls._collection)
                logger.info(f"Successfully created collection {cls._collection}")
            except errors.CollectionInvalid:
                # Collection might have been created by another process
                pass
            except Exception as e:
                logger.error(f"Failed to create collection {cls._collection}: {str(e)}")
                raise DatabaseError(f"Failed to create collection: {str(e)}")
                
        return cls._collection

    @classmethod
    def get_or_create(cls: Type[T], **filter_options) -> T:
        """Get an existing document or create a new one."""
        collection = connection.get_collection(cls.get_collection_name())
        try:
            # Try to find existing document
            if existing := collection.find_one(filter_options):
                return cls.from_mongo(existing)
                
            # Create new document if not found
            new_instance = cls(**filter_options)
            if saved := new_instance.save():
                return saved
                
            raise DatabaseError("Failed to save new document")
            
        except errors.OperationFailure as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise DatabaseError(f"Database operation failed: {str(e)}")

    @classmethod
    def from_mongo(cls: Type[T], data: dict) -> T:
        """Convert MongoDB document to model instance."""
        if not data:
            raise ValueError("Data is empty")

        id = data.pop("_id")
        return cls(**dict(data, id=id))

    def to_mongo(self: T) -> dict:
        """Convert model instance to MongoDB document."""
        # Convert the model to a dictionary
        doc = self.model_dump(by_alias=True)
        
        # Ensure the _id is present
        if '_id' not in doc and 'id' in doc:
            doc['_id'] = doc.pop('id')
        
        return doc

    def save(self: T) -> T | None:
        """Save document to MongoDB."""
        collection = connection.get_collection(self.get_collection_name())
        try:
            # Convert the document to a format MongoDB can handle
            mongo_doc = self.to_mongo()
            
            # Use the custom insert method
            connection.insert_one(collection, mongo_doc)
            
            return self
        except errors.WriteError:
            logger.exception("Failed to insert document")
            return None

    @classmethod
    def bulk_insert(cls: Type[T], documents: list[T]) -> bool:
        """Insert multiple documents to MongoDB."""
        if not documents:
            return True

        collection = connection.get_collection(cls.get_collection_name())
        try:
            # Convert documents to MongoDB-compatible format
            mongo_docs = [doc.to_mongo() for doc in documents]
            
            # Use the custom insert method
            connection.insert_many(collection, mongo_docs)
            
            return True
        except errors.BulkWriteError:
            logger.error(f"Failed to bulk insert {cls.__name__} documents")
            return False

    @classmethod
    def find(cls: Type[T], **filter_options) -> T | None:
        """Find a single document in MongoDB."""
        collection = connection.get_collection(cls.get_collection_name())
        try:
            if doc := collection.find_one(filter_options):
                return cls.from_mongo(doc)
            return None
        except errors.OperationFailure:
            logger.error("Failed to retrieve document")
            return None

    @classmethod
    def bulk_find(cls: Type[T], **filter_options) -> list[T]:
        """Find multiple documents in MongoDB."""
        collection = connection.get_collection(cls.get_collection_name())
        try:
            cursor = collection.find(filter_options)
            return [
                doc for item in cursor 
                if (doc := cls.from_mongo(item)) is not None
            ]
        except errors.OperationFailure:
            logger.error("Failed to retrieve documents")
            return []