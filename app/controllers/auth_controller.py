from fastapi import APIRouter, HTTPException, Cookie
from fastapi.responses import JSONResponse
from typing import Optional
from app.services.github_services import (get_github_access_token, get_github_user, get_github_email, find_or_create_github_user)
from app.core import GITHUB_CLIENT_ID, GITHUB_REDIRECT_URI
from fastapi.responses import RedirectResponse


from app.models.user import RegisterRequest, LoginRequest
from app.services.auth_service import (
    register_user, login_user,
    create_access_token, create_refresh_token,
    verify_refresh_token, delete_refresh_token
)

router = APIRouter(prefix="/auth", tags=["auth"])
# prefix="/auth" = like router.use('/auth') in Express

@router.post("/register")
async def register(body: RegisterRequest):
    user, error = await register_user(body.username, body.email, body.password)
    if error:
        raise HTTPException(status_code=400, detail=error)

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

    # Store refresh token in HTTP-only cookie (like in Node.js)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,      # JS can't access this cookie
        max_age=30 * 24 * 60 * 60,  # 30 days
        samesite="lax"
    )
    return response

@router.post("/login")
async def login(body: LoginRequest):
    user, error = await login_user(body.email, body.password)
    if error:
        raise HTTPException(status_code=401, detail=error)

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

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=30 * 24 * 60 * 60,
        samesite="lax"
    )
    return response

@router.post("/refresh")
async def refresh(refresh_token: Optional[str] = Cookie(None)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    user_id = await verify_refresh_token(refresh_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # Issue new access token
    access_token = create_access_token(user_id)
    return {"access_token": access_token}

@router.post("/logout")
async def logout(refresh_token: Optional[str] = Cookie(None)):
    if refresh_token:
        await delete_refresh_token(refresh_token)

    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie("refresh_token")
    return response


@router.get("/github")
async def github_login():
    # Redirect user to GitHub login page
    # Like passport.authenticate('github') in Node.js
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={GITHUB_REDIRECT_URI}"
        f"&scope=user:email"
    )
    return RedirectResponse(url=github_auth_url)

@router.get("/github/callback")
async def github_callback(code: str):
    # GitHub redirects back here with a code
    # Exchange code for access token
    github_access_token = await get_github_access_token(code)
    if not github_access_token:
        raise HTTPException(status_code=400, detail="GitHub authentication failed")

    # Get GitHub user profile
    github_user = await get_github_user(github_access_token)
    email = await get_github_email(github_access_token)

    # Find or create user in our database
    user = await find_or_create_github_user(github_user, email)

    # Create our own JWT tokens
    access_token = create_access_token(user["id"])
    refresh_token = await create_refresh_token(user["id"])

    # Redirect to frontend with access token in URL
    # Frontend will grab it and store it
    response = RedirectResponse(url=f"http://localhost:5173?access_token={access_token}")
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=30 * 24 * 60 * 60,
        samesite="lax"
    )
    return response