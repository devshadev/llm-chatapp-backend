from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from bson import ObjectId
import uuid

from app.core import (
    JWT_SECRET, JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from app.core.database import get_db
from app.core.redis import get_redis
from app.models.user import UserInDB

# Password hashing — like bcrypt in Node.js
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# --- JWT Access Token (short lived — 30 mins) ---
def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# --- Decode and verify JWT ---
def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")  # returns user_id
    except JWTError:
        return None

# --- Refresh Token (long lived — 30 days, stored in Redis) ---
async def create_refresh_token(user_id: str) -> str:
    token = str(uuid.uuid4())  # random unique string
    redis = get_redis()
    expire_seconds = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # 30 days in seconds
    # Store in Redis: key = refresh_token value, value = user_id
    await redis.setex(f"refresh:{token}", expire_seconds, user_id)
    return token

async def verify_refresh_token(token: str) -> Optional[str]:
    redis = get_redis()
    user_id = await redis.get(f"refresh:{token}")
    return user_id  # returns None if expired or not found

async def delete_refresh_token(token: str):
    redis = get_redis()
    await redis.delete(f"refresh:{token}")

# --- Register new user ---
async def register_user(username: str, email: str, password: str):
    db = get_db()

    # Check if email already exists — like findOne() in Mongoose
    existing = await db.users.find_one({"email": email})
    if existing:
        return None, "Email already registered"

    # Check if username taken
    existing_username = await db.users.find_one({"username": username})
    if existing_username:
        return None, "Username already taken"

    hashed = hash_password(password)
    user_doc = {
        "username": username,
        "email": email,
        "hashed_password": hashed,
        "github_id": None,
        "created_at": datetime.utcnow()
    }

    # Insert into MongoDB — like .save() in Mongoose
    result = await db.users.insert_one(user_doc)
    user_doc["id"] = str(result.inserted_id)
    return user_doc, None

# --- Login user ---
async def login_user(email: str, password: str):
    db = get_db()

    user = await db.users.find_one({"email": email})
    if not user:
        return None, "Invalid email or password"

    if not verify_password(password, user["hashed_password"]):
        return None, "Invalid email or password"

    user["id"] = str(user["_id"])
    return user, None