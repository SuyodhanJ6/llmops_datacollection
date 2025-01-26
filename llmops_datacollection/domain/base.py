import uuid
from abc import ABC
from typing import Any, ClassVar, Dict, Generic, Type, TypeVar

from loguru import logger
from pydantic import UUID4, BaseModel, Field
from pymongo import errors

from llmops_datacollection.domain.exceptions import ImproperlyConfigured
from llmops_datacollection.infrastructure.db.mongo import connection

T = TypeVar("T", bound="NoSQLBaseDocument")

class NoSQLBaseDocument(BaseModel, Generic[T], ABC):
    """Base document model with MongoDB integration."""
    
    id: UUID4 = Field(default_factory=uuid.uuid4)
    _collection: ClassVar[str | None] = None

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, self.__class__):
            return False
        return self.id == value.id

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def from_mongo(cls: Type[T], data: dict) -> T:
        """Convert MongoDB document to model instance."""
        if not data:
            raise ValueError("Data is empty")

        id = data.pop("_id")
        return cls(**dict(data, id=id))

    def to_mongo(self: T) -> dict:
        """Convert model instance to MongoDB document."""
        parsed = self.model_dump()
        
        if "_id" not in parsed and "id" in parsed:
            parsed["_id"] = str(parsed.pop("id"))

        return parsed

    @classmethod
    def get_collection_name(cls) -> str:
        """Get MongoDB collection name."""
        if cls._collection is None:
            raise ImproperlyConfigured(
                f"Collection name not set for {cls.__name__}"
            )
        return cls._collection

    def save(self: T) -> T | None:
        """Save document to MongoDB."""
        collection = connection.get_collection(self.get_collection_name())
        try:
            collection.insert_one(self.to_mongo())
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
            collection.insert_many(
                [doc.to_mongo() for doc in documents]
            )
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