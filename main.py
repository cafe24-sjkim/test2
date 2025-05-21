from fastapi import FastAPI, HTTPException, Depends, status # Added Depends and status
from typing import List
from datetime import timedelta # Added timedelta

from fastapi.security import OAuth2PasswordRequestForm # Added OAuth2PasswordRequestForm

# Model imports
from models.post import PostCreate, PostResponse, PostUpdate
from models.user import User, UserCreate, Token # Added User, UserCreate, Token

# Database and Auth imports
from database.utils import ( # Grouped DB utils imports
    create_post, 
    get_all_posts, 
    get_post, 
    update_post, 
    delete_post,
    create_user, # Added create_user
    get_user_by_username # Added get_user_by_username
)
from database.setup import create_db_and_tables
import auth # Added auth module

# Create database and tables
create_db_and_tables()

app = FastAPI()

# Placeholder for root endpoint (from initial setup)
@app.get("/")
async def root():
    return {"message": "Hello World, API is running!"}

# --- Authentication Endpoints ---

@app.post("/users/signup", response_model=User, status_code=status.HTTP_201_CREATED)
async def signup_new_user(user_data: UserCreate):
    db_user = get_user_by_username(username=user_data.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    hashed_password = auth.get_password_hash(user_data.password)
    # create_user in utils.py expects UserCreate and hashed_password, then returns UserInDB or None
    new_user_in_db = create_user(user=user_data, hashed_password=hashed_password)
    if not new_user_in_db:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user."
        )
    # Return as User model (which excludes hashed_password)
    return User(
        id=new_user_in_db.id,
        username=new_user_in_db.username,
        is_active=new_user_in_db.is_active
    )

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    db_user = get_user_by_username(username=form_data.username)
    if not db_user or not auth.verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- CRUD Endpoints for Posts ---

@app.post("/posts", response_model=PostResponse, status_code=201)
async def create_new_post(post: PostCreate, current_user: User = Depends(auth.get_current_active_user)):
    # Ownership logic is not implemented in this step.
    # We just ensure the user is authenticated.
    post_id = create_post(title=post.title, content=post.content)
    created_post = get_post(post_id)
    if not created_post:
        # This case should ideally not happen if create_post is successful and returns a valid ID
        raise HTTPException(status_code=500, detail="Failed to create post.")
    return PostResponse(**created_post)

@app.get("/posts", response_model=List[PostResponse])
async def read_all_posts(current_user: User = Depends(auth.get_current_active_user)):
    # Now requires authentication
    posts = get_all_posts()
    return [PostResponse(**post) for post in posts]

@app.get("/posts/{post_id}", response_model=PostResponse)
async def read_post(post_id: int, current_user: User = Depends(auth.get_current_active_user)):
    # Now requires authentication
    post = get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostResponse(**post)

@app.put("/posts/{post_id}", response_model=PostResponse)
async def update_existing_post(post_id: int, post_update: PostUpdate, current_user: User = Depends(auth.get_current_active_user)):
    # Ownership logic is not implemented in this step.
    # We just ensure the user is authenticated.
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
async def remove_post(post_id: int, current_user: User = Depends(auth.get_current_active_user)):
    # Ownership logic is not implemented in this step.
    # We just ensure the user is authenticated.
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
