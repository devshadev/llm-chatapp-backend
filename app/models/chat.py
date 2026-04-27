from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- Single message inside a chat ---
class Message(BaseModel):
    id: Optional[str] = None
    chat_id: str
    role: str  # "user" or "assistant"
    content: str
    created_at: datetime = datetime.utcnow()

# --- A conversation thread ---
class Chat(BaseModel):
    id: Optional[str] = None
    user_id: str
    title: str = "New Chat"
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

# --- Request to create a new chat ---
class CreateChatRequest(BaseModel):
    title: Optional[str] = "New Chat"

# --- Request to send a message ---
class SendMessageRequest(BaseModel):
    content: str

# --- Response shape for a chat with its messages ---
class ChatResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime