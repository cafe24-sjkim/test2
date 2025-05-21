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

# Helper function to clear tables for test isolation
def clear_all_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts")
    cursor.execute("DELETE FROM users") # Also clear users table
    conn.commit()
    conn.close()

# Global variable to store test user credentials and token
test_user_data = {"username": "testuser@example.com", "password": "testpassword"}
auth_token = None

# Basic test to ensure the test setup is working
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World, API is running!"}

@pytest.fixture(autouse=True)
def run_before_and_after_tests():
    """Fixture to execute setup and cleanup for all tests"""
    clear_all_tables()
    global auth_token # Ensure auth_token is reset for each test scenario
    auth_token = None 
    yield # this is where the testing happens

# Helper function to get an auth token
def get_auth_token(username_override=None, password_override=None):
    global auth_token
    # if auth_token: # Caching token can cause issues if tests modify user state
    #     return auth_token

    # 1. Ensure user exists (or create one)
    signup_data = {
        "username": username_override or test_user_data["username"],
        "password": password_override or test_user_data["password"]
    }
    # Try to sign up, ignore if user already exists (400)
    client.post("/users/signup", json=signup_data) 

    # 2. Log in to get token
    login_data = {
        "username": username_override or test_user_data["username"],
        "password": password_override or test_user_data["password"]
    }
    response = client.post("/token", data=login_data) # x-www-form-urlencoded
    if response.status_code == 200:
        auth_token = response.json()["access_token"]
        return auth_token
    else:
        # This will cause tests relying on this function to fail, which is intended
        # if login itself is failing.
        print(f"Failed to get token: {response.status_code} {response.text}")
        return None


# --- User Authentication Tests ---

def test_user_signup():
    response = client.post("/users/signup", json=test_user_data)
    assert response.status_code == 201 # HTTP 201 Created
    data = response.json()
    assert data["username"] == test_user_data["username"]
    assert "id" in data
    assert data["is_active"] is True # Default value

    # Test duplicate username
    response_duplicate = client.post("/users/signup", json=test_user_data)
    assert response_duplicate.status_code == 400 # HTTP 400 Bad Request
    assert response_duplicate.json()["detail"] == "Username already registered"

def test_user_login_and_get_token():
    # 1. Create user first
    client.post("/users/signup", json=test_user_data) # Ensure user exists

    # 2. Test successful login
    login_payload = {"username": test_user_data["username"], "password": test_user_data["password"]}
    response = client.post("/token", data=login_payload) # x-www-form-urlencoded
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Store token for other tests if needed (though get_auth_token is preferred)
    global auth_token
    auth_token = data["access_token"]

    # 3. Test login with incorrect password
    login_payload_wrong_pass = {"username": test_user_data["username"], "password": "wrongpassword"}
    response_wrong_pass = client.post("/token", data=login_payload_wrong_pass)
    assert response_wrong_pass.status_code == 401
    assert response_wrong_pass.json()["detail"] == "Incorrect username or password"

    # 4. Test login with non-existent username
    login_payload_non_existent_user = {"username": "nouser@example.com", "password": "somepassword"}
    response_non_existent_user = client.post("/token", data=login_payload_non_existent_user)
    assert response_non_existent_user.status_code == 401
    assert response_non_existent_user.json()["detail"] == "Incorrect username or password"


# --- Post API Tests (with Authentication) ---

def test_create_post_authenticated():
    token = get_auth_token()
    assert token is not None, "Failed to get auth token for test"
    headers = {"Authorization": f"Bearer {token}"}
    post_payload = {"title": "Authenticated Post", "content": "Content created with auth"}
    response = client.post("/posts", json=post_payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == post_payload["title"]
    assert data["content"] == post_payload["content"]
    assert "id" in data

def test_create_post_unauthenticated():
    post_payload = {"title": "Unauthenticated Post", "content": "Should fail"}
    response = client.post("/posts", json=post_payload) # No headers
    assert response.status_code == 401 # HTTP 401 Unauthorized
    assert response.json()["detail"] == "Not authenticated" # Or your specific message

# Renamed to reflect it's now an authenticated endpoint
def test_get_all_posts_empty_authenticated(): 
    token = get_auth_token()
    assert token is not None, "Failed to get auth token for test"
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/posts", headers=headers)
    assert response.status_code == 200
    assert response.json() == []

def test_get_all_posts_unauthenticated():
    response = client.get("/posts") # No headers
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

# Renamed to reflect it's now an authenticated endpoint for the GET part too
def test_get_post_authenticated(): 
    token = get_auth_token()
    assert token is not None, "Failed to get auth token for test"
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create a post (already requires auth, headers are used)
    post_data = {"title": "Get Me Authenticated", "content": "Content to get with auth"}
    create_response = client.post("/posts", json=post_data, headers=headers)
    assert create_response.status_code == 201
    created_post_id = create_response.json()["id"]

    # 2. Test the GET endpoint for this specific post, now requiring auth
    response = client.get(f"/posts/{created_post_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == post_data["title"]
    assert data["content"] == post_data["content"]
    assert data["id"] == created_post_id

def test_get_specific_post_unauthenticated():
    # 1. Create a post first (needs auth to create)
    token = get_auth_token()
    assert token is not None, "Failed to get auth token for test"
    headers = {"Authorization": f"Bearer {token}"}
    post_data = {"title": "For Unauth Get", "content": "Content"}
    create_response = client.post("/posts", json=post_data, headers=headers)
    assert create_response.status_code == 201
    created_post_id = create_response.json()["id"]

    # 2. Attempt to GET the post without auth
    response = client.get(f"/posts/{created_post_id}") # No headers
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

# Renamed to reflect it's now an authenticated endpoint
def test_get_post_not_found_authenticated(): 
    token = get_auth_token()
    assert token is not None, "Failed to get auth token for test"
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/posts/99999", headers=headers) # Use a high number
    assert response.status_code == 404 # Post not found, even if authenticated
    assert response.json() == {"detail": "Post not found"}

def test_update_post_authenticated():
    token = get_auth_token()
    assert token is not None, "Failed to get auth token for test"
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create a post first
    original_post_data = {"title": "Original Title", "content": "Original Content"}
    create_response = client.post("/posts", json=original_post_data, headers=headers)
    assert create_response.status_code == 201
    created_post_id = create_response.json()["id"]

    # 2. Update the post
    update_data = {"title": "Updated Title", "content": "Updated Content"}
    response = client.put(f"/posts/{created_post_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["content"] == update_data["content"]
    assert data["id"] == created_post_id

def test_update_post_unauthenticated():
    # 1. Create a post first (needs auth to create)
    token = get_auth_token()
    assert token is not None, "Failed to get auth token for test"
    headers = {"Authorization": f"Bearer {token}"}
    original_post_data = {"title": "Original for Unauth Update", "content": "Content"}
    create_response = client.post("/posts", json=original_post_data, headers=headers)
    assert create_response.status_code == 201
    created_post_id = create_response.json()["id"]

    # 2. Attempt to update without auth
    update_data = {"title": "Updated Title Unauth", "content": "Updated Content Unauth"}
    response = client.put(f"/posts/{created_post_id}", json=update_data) # No headers
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_update_post_not_found_authenticated(): # Renamed for clarity
    token = get_auth_token()
    assert token is not None, "Failed to get auth token for test"
    headers = {"Authorization": f"Bearer {token}"}
    update_data = {"title": "Non Existent", "content": "Update Content"}
    response = client.put("/posts/99999", json=update_data, headers=headers) # Use a high number
    assert response.status_code == 404 # Post not found, even if authenticated
    assert response.json() == {"detail": "Post not found"}


def test_delete_post_authenticated():
    token = get_auth_token()
    assert token is not None, "Failed to get auth token for test"
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a post first
    post_data = {"title": "To Be Deleted", "content": "Delete this content"}
    create_response = client.post("/posts", json=post_data, headers=headers)
    assert create_response.status_code == 201
    created_post_id = create_response.json()["id"]

    # 2. Send an authenticated DELETE request
    delete_response = client.delete(f"/posts/{created_post_id}", headers=headers)
    assert delete_response.status_code == 204

    # 3. Verify the post is deleted by trying to GET it (public endpoint)
    get_response = client.get(f"/posts/{created_post_id}")
    assert get_response.status_code == 404

def test_delete_post_unauthenticated():
    # 1. Create a post first (needs auth)
    token = get_auth_token()
    assert token is not None, "Failed to get auth token for test"
    headers = {"Authorization": f"Bearer {token}"}
    post_data = {"title": "To Be Deleted Unauth", "content": "Content"}
    create_response = client.post("/posts", json=post_data, headers=headers)
    assert create_response.status_code == 201
    created_post_id = create_response.json()["id"]

    # 2. Attempt to delete without auth
    delete_response = client.delete(f"/posts/{created_post_id}") # No headers
    assert delete_response.status_code == 401
    assert delete_response.json()["detail"] == "Not authenticated"


def test_delete_post_not_found_authenticated(): # Renamed for clarity
    token = get_auth_token()
    assert token is not None, "Failed to get auth token for test"
    headers = {"Authorization": f"Bearer {token}"}
    response = client.delete("/posts/99999", headers=headers) # Use a high number
    assert response.status_code == 404 # Post not found, even if authenticated
    assert response.json() == {"detail": "Post not found"}

# End of test functions
# Note: `test_update_post_not_found` and `test_delete_post_not_found` were renamed
# to `_authenticated` to clarify they test the "not found" aspect while still being authenticated.
# The unauthenticated versions for these "not found" scenarios would also result in 401
# if the path itself was protected, or 404 if path is public but item not found.
# For PUT/DELETE /posts/{id}, the path itself requires auth, so 401 takes precedence over 404
# if no token or invalid token is provided.
# If a valid token is provided but for a non-existent post_id, then 404 is correct.
