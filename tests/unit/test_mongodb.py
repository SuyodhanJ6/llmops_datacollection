import pytest
from unittest.mock import Mock, patch

from llmops_datacollection.domain.documents import UserDocument
from llmops_datacollection.domain.exceptions import DatabaseError

def test_user_creation():
    """Test user document creation."""
    user = UserDocument(
        first_name="John",
        last_name="Doe"
    )
    assert user.full_name == "John Doe"
    assert user.id is not None

def test_user_save(test_db):
    """Test saving user to database."""
    user = UserDocument(
        first_name="Jane",
        last_name="Doe"
    )
    saved_user = user.save()
    assert saved_user is not None
    assert saved_user.id == user.id

def test_user_find(test_user):
    """Test finding user in database."""
    found_user = UserDocument.find(first_name=test_user.first_name)
    assert found_user is not None
    assert found_user.id == test_user.id

def test_user_get_or_create():
    """Test get_or_create functionality."""
    # First creation
    user1 = UserDocument.get_or_create(
        first_name="Alice",
        last_name="Smith"
    )
    assert user1 is not None
    
    # Should retrieve existing
    user2 = UserDocument.get_or_create(
        first_name="Alice",
        last_name="Smith"
    )
    assert user2.id == user1.id

def test_user_bulk_insert():
    """Test bulk insertion of users."""
    users = [
        UserDocument(first_name=f"User{i}", last_name="Test")
        for i in range(3)
    ]
    assert UserDocument.bulk_insert(users) is True
    
    # Verify all users were saved
    found_users = UserDocument.bulk_find(last_name="Test")
    assert len(found_users) == 3

@pytest.mark.parametrize("first_name,last_name", [
    ("John", "Doe"),
    ("Jane", "Smith"),
    ("Alice", "Johnson")
])
def test_multiple_users(first_name, last_name):
    """Test creating multiple users with different names."""
    user = UserDocument(
        first_name=first_name,
        last_name=last_name
    )
    saved_user = user.save()
    assert saved_user is not None
    assert saved_user.full_name == f"{first_name} {last_name}"