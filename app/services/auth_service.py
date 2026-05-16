from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.responses import JSONResponse, RedirectResponse
import uuid

from app.core import (
    JWT_SECRET, JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from app.core.database import get_db
from app.core.redis import get_redis

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
COOKIE_MAX_AGE = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


async def create_refresh_token(user_id: str) -> str:
    token = str(uuid.uuid4())
    redis = get_redis()
    await redis.setex(f"refresh:{token}", COOKIE_MAX_AGE, user_id)
    return token


async def verify_refresh_token(token: str) -> Optional[str]:
    redis = get_redis()
    return await redis.get(f"refresh:{token}")


async def delete_refresh_token(token: str):
    redis = get_redis()
    await redis.delete(f"refresh:{token}")


def _set_refresh_cookie(response, refresh_token: str):
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=COOKIE_MAX_AGE,
        samesite="lax"
    )
    return response


# --- Register new user ---
async def register_user(username: str, email: str, password: str):
    db = get_db()

    if await db.users.find_one({"email": email}):
        return None, "Email already registered"

    if await db.users.find_one({"username": username}):
        return None, "Username already taken"

    hashed = hash_password(password)
    user_doc = {
        "username": username,
        "email": email,
        "hashed_password": hashed,
        "github_id": None,
        "created_at": datetime.utcnow()
    }
    result = await db.users.insert_one(user_doc)
    user_doc["id"] = str(result.inserted_id)
    return user_doc, None


# --- Login user ---
async def login_user(email: str, password: str):
    db = get_db()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(password, user["hashed_password"]):
        return None, "Invalid email or password"
    user["id"] = str(user["_id"])
    return user, None


# --- Register and build full response ---
async def register_and_respond(username: str, email: str, password: str):
    user, error = await register_user(username, email, password)
    if error:
        return None, error

    access_token = create_access_token(user["id"])
    refresh_token = await create_refresh_token(user["id"])

    response = JSONResponse(content={
        "access_token": access_token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    })
    return _set_refresh_cookie(response, refresh_token), None


# --- Login and build full response ---
async def login_and_respond(email: str, password: str):
    user, error = await login_user(email, password)
    if error:
        return None, error

    access_token = create_access_token(user["id"])
    refresh_token = await create_refresh_token(user["id"])

    response = JSONResponse(content={
        "access_token": access_token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    })
    return _set_refresh_cookie(response, refresh_token), None


# --- Refresh access token ---
async def refresh_access_token(refresh_token: Optional[str]):
    if not refresh_token:
        return None, "No refresh token"
    user_id = await verify_refresh_token(refresh_token)
    if not user_id:
        return None, "Invalid or expired refresh token"
    return create_access_token(user_id), None


# --- Logout ---
async def logout_user(refresh_token: Optional[str]) -> JSONResponse:
    if refresh_token:
        await delete_refresh_token(refresh_token)
    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie("refresh_token")
    return response


# --- GitHub OAuth — full callback flow ---
async def handle_github_callback(
    github_user: dict,
    email: str,
    frontend_url: str,
) -> RedirectResponse:
    from app.services.github_services import find_or_create_github_user

    user = await find_or_create_github_user(github_user, email)
    access_token = create_access_token(user["id"])
    refresh_token = await create_refresh_token(user["id"])

    response = RedirectResponse(url=f"{frontend_url}?access_token={access_token}")
    return _set_refresh_cookie(response, refresh_token)