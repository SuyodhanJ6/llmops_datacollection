from typing import Optional

from pydantic import UUID4, Field

from llmops_datacollection.domain.base import NoSQLBaseDocument

class UserDocument(NoSQLBaseDocument):
    """User document model."""
    
    first_name: str
    last_name: str
    _collection = "users"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

class ContentDocument(NoSQLBaseDocument):
    """Base content document model."""
    
    content: dict
    platform: str
    author_id: UUID4 = Field(alias="author_id")
    author_full_name: str = Field(alias="author_full_name")

class ArticleDocument(ContentDocument):
    """Article document model."""
    
    link: str
    title: str
    _collection = "articles"

class PostDocument(ContentDocument):
    """Social media post document model."""
    
    link: Optional[str] = None
    image: Optional[str] = None
    _collection = "posts"

class RepositoryDocument(ContentDocument):
    """GitHub repository document model."""
    
    name: str
    link: str
    _collection = "repositories"