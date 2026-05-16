from fastapi import APIRouter, HTTPException, Cookie
from fastapi.responses import RedirectResponse
from typing import Optional

from app.core import GITHUB_CLIENT_ID, GITHUB_REDIRECT_URI, FRONTEND_URL
from app.models.user import RegisterRequest, LoginRequest
from app.services.auth_service import (
    register_and_respond,
    login_and_respond,
    refresh_access_token,
    logout_user,
    handle_github_callback
)
from app.services.github_services import (
    get_github_access_token,
    get_github_user,
    get_github_email,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(body: RegisterRequest):
    response, error = await register_and_respond(body.username, body.email, body.password)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return response


@router.post("/login")
async def login(body: LoginRequest):
    response, error = await login_and_respond(body.email, body.password)
    if error:
        raise HTTPException(status_code=401, detail=error)
    return response


@router.post("/refresh")
async def refresh(refresh_token: Optional[str] = Cookie(None)):
    access_token, error = await refresh_access_token(refresh_token)
    if error:
        raise HTTPException(status_code=401, detail=error)
    return {"access_token": access_token}


@router.post("/logout")
async def logout(refresh_token: Optional[str] = Cookie(None)):
    return await logout_user(refresh_token)


@router.get("/github")
async def github_login():
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={GITHUB_REDIRECT_URI}"
        f"&scope=user:email"
    )
    return RedirectResponse(url=github_auth_url)


@router.get("/github/callback")
async def github_callback(code: str):
    github_access_token = await get_github_access_token(code)
    if not github_access_token:
        raise HTTPException(status_code=400, detail="GitHub authentication failed")

    github_user = await get_github_user(github_access_token)
    email = await get_github_email(github_access_token)

    return await handle_github_callback(
        github_user=github_user,
        email=email,
        frontend_url=FRONTEND_URL
    )