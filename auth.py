# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

# Adjust model and util paths according to your project structure
# Assuming models and database are at the same level as auth.py or in PYTHONPATH
from models.user import TokenData, UserInDB # User model is not directly used here but UserInDB is
from database.utils import get_user_by_username

# Configuration
SECRET_KEY = "a_very_secret_key_generated_by_openssl_rand_hex_32" # Replace with your actual secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
# The tokenUrl should point to the endpoint that issues tokens, e.g., /login or /auth/token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token") # Assuming /token is the login endpoint

# --- Password Utilities ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

# --- Token Utilities ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a new access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- User Authentication/Authorization Utilities ---
async def get_current_user_from_token(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """
    Decodes the JWT token, retrieves the user based on the username in the token,
    and returns the user object if valid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub") # "sub" is a standard claim for subject (username)
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_username(username=token_data.username) # This function is synchronous
    if user is None:
        raise credentials_exception
    return user # UserInDB instance

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user_from_token)) -> UserInDB:
    """
    Checks if the current user (obtained from the token) is active.
    Raises an HTTPException if the user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user
