from fastapi import FastAPI, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from typing import Optional
from app.core.database import connect_db, close_db
from app.core.redis import connect_redis, close_redis
from app.controllers.auth_controller import router as auth_router
from app.core.dependencies import get_current_user
from app.controllers.chat_controller import router as chat_router
from app.core.db_init import initialize_indexes

security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    await connect_redis()
    await initialize_indexes()
    yield
    await close_db()
    await close_redis()

app = FastAPI(title="LLM Chat App", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://llm-chatapp-backend.vercel.app","http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

@app.get("/")
async def root():
    return {"message": "LLM Chat API is running 🚀"}

@app.get("/me")
async def get_me(current_user = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"]
    }

app.include_router(chat_router)  