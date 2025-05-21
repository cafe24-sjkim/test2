from fastapi import FastAPI, HTTPException
from typing import List

from models.post import PostCreate, PostResponse, PostUpdate
from database.utils import create_post, get_all_posts, get_post, update_post, delete_post
from database.setup import create_db_and_tables

# Create database and tables
create_db_and_tables()

app = FastAPI()

# Placeholder for root endpoint (from initial setup)
@app.get("/")
async def root():
    return {"message": "Hello World, API is running!"}

# --- CRUD Endpoints for Posts ---

@app.post("/posts", response_model=PostResponse, status_code=201)
async def create_new_post(post: PostCreate):
    post_id = create_post(title=post.title, content=post.content)
    created_post = get_post(post_id)
    if not created_post:
        # This case should ideally not happen if create_post is successful and returns a valid ID
        raise HTTPException(status_code=500, detail="Failed to create post.")
    return PostResponse(**created_post)

@app.get("/posts", response_model=List[PostResponse])
async def read_all_posts():
    posts = get_all_posts()
    return [PostResponse(**post) for post in posts]

@app.get("/posts/{post_id}", response_model=PostResponse)
async def read_post(post_id: int):
    post = get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostResponse(**post)

@app.put("/posts/{post_id}", response_model=PostResponse)
async def update_existing_post(post_id: int, post_update: PostUpdate):
    # Check if post exists first
    existing_post = get_post(post_id)
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")

    updated_successfully = update_post(post_id, title=post_update.title, content=post_update.content)
    
    if not updated_successfully:
        # This might indicate an issue with the update process itself, even if the post exists.
        # Depending on `update_post` behavior, this might be redundant if it already raises an error
        # or if `get_post` below handles it.
        # For now, let's assume `update_post` returning False means "update did not happen for some reason".
        # We will rely on the subsequent get_post to confirm the state.
        pass # Or raise an HTTPException if update_post is expected to always succeed if post exists

    updated_post_data = get_post(post_id)
    if not updated_post_data:
        # This would be unusual if the post existed and update_post didn't delete it
        raise HTTPException(status_code=404, detail="Post not found after attempting update.")
        
    return PostResponse(**updated_post_data)

@app.delete("/posts/{post_id}", status_code=204)
async def remove_post(post_id: int):
    # First, check if the post exists to give a 404 if trying to delete a non-existent post.
    existing_post = get_post(post_id)
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")

    deleted_successfully = delete_post(post_id)
    
    if not deleted_successfully:
        # This case implies the post existed (checked above) but deletion failed for some other reason.
        # This could be a server error or an issue with the delete_post function's logic if it
        # can return False even for existing posts (e.g., database constraints, though not in this simple schema).
        raise HTTPException(status_code=500, detail="Failed to delete post.")
    
    # No content to return, status code 204 handles this.
    return
