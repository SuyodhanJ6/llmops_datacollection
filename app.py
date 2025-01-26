# app.py
from llmops_datacollection.domain.documents import UserDocument

# Create test user
user = UserDocument(
    first_name="Test",
    last_name="User"
)

# Save to database
saved_user = user.save()

# Print result
print(f"Created user: {saved_user.full_name} with ID: {saved_user.id}")