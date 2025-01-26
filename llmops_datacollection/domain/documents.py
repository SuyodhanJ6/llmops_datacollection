# llmops_datacollection/domain/documents.py
from typing import Optional, ClassVar
from pydantic import BaseModel, Field
from pydantic.types import UUID4  # Import UUID4 from pydantic.types
from .base import NoSQLBaseDocument

class UserDocument(NoSQLBaseDocument):
    """User document model."""
    
    first_name: str
    last_name: str
    _collection: ClassVar[str] = "users"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

class ContentDocument(NoSQLBaseDocument):
    """Base content document model."""
    
    content: dict
    platform: str
    author_id: UUID4 = Field(alias="author_id")  # Using UUID4
    author_full_name: str = Field(alias="author_full_name")

class ArticleDocument(ContentDocument):
    """Article document model."""
    
    link: str
    title: str
    _collection: ClassVar[str] = "articles"

class PostDocument(ContentDocument):
    """Social media post document model."""
    
    link: Optional[str] = None
    image: Optional[str] = None
    _collection: ClassVar[str] = "posts"

class RepositoryDocument(ContentDocument):
    """GitHub repository document model."""
    
    name: str
    link: str
    _collection: ClassVar[str] = "repositories"