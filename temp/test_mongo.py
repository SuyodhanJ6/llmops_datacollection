from llmops_datacollection.infrastructure.db.mongo import connection
from llmops_datacollection.domain.documents import UserDocument

# Test direct MongoDB access
def test_connection():
    # Test insert
    test_user = UserDocument(
        first_name="Test",
        last_name="User"
    )
    
    collection = connection.get_collection(UserDocument._collection)
    result = connection.insert_one(collection, test_user.to_mongo())
    print(f"Insert result: {result.inserted_id}")
    
    # Test find
    found = collection.find_one({"first_name": "Test"})
    print(f"Found document: {found}")

if __name__ == "__main__":
    test_connection()