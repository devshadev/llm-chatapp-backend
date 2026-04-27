# GitHub OAuth flow — like passport.js GitHub strategy in Node.js
import httpx
from app.core import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GITHUB_REDIRECT_URI
from app.core.database import get_db
from datetime import datetime

async def get_github_access_token(code: str) -> str:
    # Exchange the code GitHub gave us for an actual access token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_REDIRECT_URI,
            }
        )
        data = response.json()
        return data.get("access_token")

async def get_github_user(access_token: str) -> dict:
    # Use the access token to get the user's GitHub profile
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
        )
        return response.json()

async def get_github_email(access_token: str) -> str:
    # Get user's primary email from GitHub
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
        )
        emails = response.json()
        # Find primary email
        for email in emails:
            if email.get("primary") and email.get("verified"):
                return email.get("email")
        return None

async def find_or_create_github_user(github_user: dict, email: str) -> dict:
    db = get_db()

    github_id = str(github_user.get("id"))
    username = github_user.get("login")  # GitHub username

    # Check if user already exists with this github_id
    user = await db.users.find_one({"github_id": github_id})
    if user:
        user["id"] = str(user["_id"])
        return user

    # Check if email already exists (user registered with password before)
    if email:
        user = await db.users.find_one({"email": email})
        if user:
            # Link GitHub to existing account
            await db.users.update_one(
                {"email": email},
                {"$set": {"github_id": github_id}}
            )
            user["id"] = str(user["_id"])
            return user

    # Create brand new user via GitHub
    # Make sure username is unique
    existing_username = await db.users.find_one({"username": username})
    if existing_username:
        username = f"{username}_{github_id}"  # e.g. "johndoe_12345678"

    user_doc = {
        "username": username,
        "email": email or f"{github_id}@github.com",
        "hashed_password": None,  # No password for GitHub users
        "github_id": github_id,
        "created_at": datetime.utcnow()
    }

    result = await db.users.insert_one(user_doc)
    user_doc["id"] = str(result.inserted_id)
    return user_doc