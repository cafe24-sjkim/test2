import sqlite3
from typing import Optional, List, Dict, Any
from models.user import UserCreate, UserInDB # Added UserCreate and UserInDB

DATABASE_URL = "posts.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

def create_post(title: str, content: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO posts (title, content) VALUES (?, ?)", (title, content))
    conn.commit()
    post_id = cursor.lastrowid
    conn.close()
    if post_id is None:
        raise Exception("Failed to create post, lastrowid is None")
    return post_id

def get_post(post_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content FROM posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    conn.close()
    if post:
        return dict(post)
    return None

def get_all_posts() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content FROM posts")
    posts = cursor.fetchall()
    conn.close()
    return [dict(post) for post in posts]

def update_post(post_id: int, title: Optional[str] = None, content: Optional[str] = None) -> bool:
    if title is None and content is None:
        return False  # Nothing to update

    conn = get_db_connection()
    cursor = conn.cursor()
    
    updates: List[str] = []
    params: List[Any] = []

    if title is not None:
        updates.append("title = ?")
        params.append(title)
    if content is not None:
        updates.append("content = ?")
        params.append(content)
    
    params.append(post_id)
    
    query = f"UPDATE posts SET {', '.join(updates)} WHERE id = ?"
    
    cursor.execute(query, tuple(params))
    conn.commit()
    
    updated_rows = cursor.rowcount
    conn.close()
    
    return updated_rows > 0

def delete_post(post_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    deleted_rows = cursor.rowcount
    conn.close()
    return deleted_rows > 0

# --- User related database functions ---

def get_user_by_username(username: str) -> Optional[UserInDB]: # Forward declaration for create_user
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, hashed_password, is_active FROM users WHERE username = ?", (username,))
    user_row = cursor.fetchone()
    conn.close()
    if user_row:
        return UserInDB(**dict(user_row))
    return None

def create_user(user: UserCreate, hashed_password: str) -> Optional[UserInDB]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
            (user.username, hashed_password)
        )
        conn.commit()
        # Fetch the user back to get ID and defaults like is_active
        created_user = get_user_by_username(user.username)
        return created_user
    except sqlite3.IntegrityError: # Username already exists
        return None
    finally:
        conn.close()

def get_user(user_id: int) -> Optional[UserInDB]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, hashed_password, is_active FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    conn.close()
    if user_row:
        return UserInDB(**dict(user_row))
    return None
