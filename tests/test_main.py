import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the parent directory to the sys.path to allow imports from main, models, etc.
# This is a common way to handle imports in test files when the test directory is a sibling to the main package.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app # This should now work
from models.post import PostResponse # For response validation if needed
from database.setup import create_db_and_tables
from database.utils import get_db_connection # To potentially clean up

# Initialize the TestClient
client = TestClient(app)

# Ensure the database and tables are created before running tests
# This is important if tests are run independently and the main app startup isn't triggered.
create_db_and_tables()

# Helper function to clear posts table for test isolation if needed
def clear_posts_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts")
    conn.commit()
    conn.close()

# Basic test to ensure the test setup is working
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World, API is running!"}

# Placeholder for tests
# Test functions will be added below this line
# Note: For simplicity in this exercise, tests will interact with the same 'posts.db'.
# In a real-world scenario, you'd use a separate test database or more sophisticated cleanup.
# We'll add a fixture to clear the table before each test.

@pytest.fixture(autouse=True)
def run_before_and_after_tests():
    """Fixture to execute setup and cleanup"""
    clear_posts_table()
    yield # this is where the testing happens
    # clear_posts_table() # Optional: clear after each test if not handled by next test's setup

# Test functions will follow here
def test_create_post():
    response = client.post("/posts", json={"title": "Test Post", "content": "Test Content"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Post"
    assert data["content"] == "Test Content"
    assert "id" in data

def test_get_all_posts_empty():
    # The @pytest.fixture(autouse=True) run_before_and_after_tests clears the table
    response = client.get("/posts")
    assert response.status_code == 200
    assert response.json() == []

def test_get_post():
    # Create a post first
    post_data = {"title": "Get Me", "content": "Content to get"}
    create_response = client.post("/posts", json=post_data)
    assert create_response.status_code == 201
    created_post_id = create_response.json()["id"]

    # Send a GET request to /posts/{post_id}
    response = client.get(f"/posts/{created_post_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == post_data["title"]
    assert data["content"] == post_data["content"]
    assert data["id"] == created_post_id

def test_get_post_not_found():
    response = client.get("/posts/99999") # Use a high number to avoid collision
    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}

def test_update_post():
    # Create a post first
    post_data = {"title": "Original Title", "content": "Original Content"}
    create_response = client.post("/posts", json=post_data)
    assert create_response.status_code == 201
    created_post_id = create_response.json()["id"]

    # Data for updating the post
    update_data = {"title": "Updated Title", "content": "Updated Content"}
    response = client.put(f"/posts/{created_post_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["content"] == update_data["content"]
    assert data["id"] == created_post_id

def test_update_post_not_found():
    update_data = {"title": "Non Existent", "content": "Update Content"}
    response = client.put("/posts/99999", json=update_data) # Use a high number
    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}

def test_delete_post():
    # Create a post first
    post_data = {"title": "To Be Deleted", "content": "Delete this content"}
    create_response = client.post("/posts", json=post_data)
    assert create_response.status_code == 201
    created_post_id = create_response.json()["id"]

    # Send a DELETE request
    delete_response = client.delete(f"/posts/{created_post_id}")
    assert delete_response.status_code == 204

    # Verify the post is deleted by trying to GET it
    get_response = client.get(f"/posts/{created_post_id}")
    assert get_response.status_code == 404

def test_delete_post_not_found():
    response = client.delete("/posts/99999") # Use a high number
    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}

# End of test functions
