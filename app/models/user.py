from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# --- Database document shape (what gets stored in MongoDB) ---
class UserInDB(BaseModel):
    id: Optional[str] = None
    username: str
    email: str
    hashed_password: Optional[str] = None  # Optional because GitHub OAuth users have no password
    github_id: Optional[str] = None        # For GitHub OAuth users
    created_at: datetime = datetime.utcnow()

# --- Request body for registration (what frontend sends) ---
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

# --- Request body for login ---
class LoginRequest(BaseModel):
    email: str
    password: str

# --- What we send back to frontend (never send hashed_password!) ---
class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime