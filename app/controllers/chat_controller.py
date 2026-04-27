from app.services.llm_service import get_llm_response
from fastapi import APIRouter, HTTPException, Depends
from app.core.dependencies import get_current_user
from app.models.chat import CreateChatRequest, SendMessageRequest
from app.services.chat_service import (
    create_chat, get_user_chats, get_chat,
    delete_chat, save_message, get_chat_messages,
    update_chat_title
)
from fastapi.responses import StreamingResponse
from app.services.llm_service import get_llm_response, stream_llm_response
import json

router = APIRouter(prefix="/chats", tags=["chats"])

# --- Create a new chat ---
@router.post("/")
async def create_new_chat(
    body: CreateChatRequest,
    current_user = Depends(get_current_user)  # protected route
):
    chat = await create_chat(current_user["id"], body.title)
    return {
        "id": chat["id"],
        "title": chat["title"],
        "created_at": chat["created_at"],
        "updated_at": chat["updated_at"]
    }

# --- Get all chats for current user ---
@router.get("/")
async def get_chats(current_user = Depends(get_current_user)):
    chats = await get_user_chats(current_user["id"])
    return [
        {
            "id": chat["id"],
            "title": chat["title"],
            "created_at": chat["created_at"],
            "updated_at": chat["updated_at"]
        }
        for chat in chats
    ]

# --- Get a single chat with its messages ---
@router.get("/{chat_id}")
async def get_single_chat(
    chat_id: str,
    current_user = Depends(get_current_user)
):
    chat = await get_chat(chat_id, current_user["id"])
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = await get_chat_messages(chat_id, current_user["id"])
    return {
        "id": chat["id"],
        "title": chat["title"],
        "created_at": chat["created_at"],
        "updated_at": chat["updated_at"],
        "messages": [
            {
                "id": msg["id"],
                "role": msg["role"],
                "content": msg["content"],
                "created_at": msg["created_at"]
            }
            for msg in messages
        ]
    }

# --- Update chat title ---
@router.patch("/{chat_id}")
async def update_title(
    chat_id: str,
    body: CreateChatRequest,
    current_user = Depends(get_current_user)
):
    updated = await update_chat_title(chat_id, current_user["id"], body.title)
    if not updated:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Title updated"}

# --- Delete a chat ---
@router.delete("/{chat_id}")
async def delete_single_chat(
    chat_id: str,
    current_user = Depends(get_current_user)
):
    deleted = await delete_chat(chat_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat deleted"}

# --- Get messages for a chat ---
@router.get("/{chat_id}/messages")
async def get_messages(
    chat_id: str,
    current_user = Depends(get_current_user)
):
    messages = await get_chat_messages(chat_id, current_user["id"])
    if messages is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return [
        {
            "id": msg["id"],
            "role": msg["role"],
            "content": msg["content"],
            "created_at": msg["created_at"]
        }
        for msg in messages
    ]

# --- Send a message and get LLM response ---
@router.post("/{chat_id}/messages")
async def send_message(
    chat_id: str,
    body: SendMessageRequest,
    current_user = Depends(get_current_user)
):
    # Verify chat belongs to user
    chat = await get_chat(chat_id, current_user["id"])
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Save user message
    user_message = await save_message(chat_id, "user", body.content)

    # Get LLM response
    try:
        llm_reply = await get_llm_response(body.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    # Save assistant response
    assistant_message = await save_message(chat_id, "assistant", llm_reply)

    return {
        "user_message": {
            "id": user_message["id"],
            "role": user_message["role"],
            "content": user_message["content"],
            "created_at": user_message["created_at"]
        },
        "assistant_message": {
            "id": assistant_message["id"],
            "role": assistant_message["role"],
            "content": assistant_message["content"],
            "created_at": assistant_message["created_at"]
        }
    }


@router.post("/{chat_id}/messages/stream")
async def send_message_stream(
    chat_id: str,
    body: SendMessageRequest,
    current_user = Depends(get_current_user)
):
    chat = await get_chat(chat_id, current_user["id"])
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Save user message immediately
    await save_message(chat_id, "user", body.content)

    full_response = []

    async def generate():
        async for token in stream_llm_response(body.content):
            full_response.append(token)
            # Send each token as SSE (Server-Sent Events)
            yield f"data: {json.dumps({'token': token})}\n\n"

        # After streaming done, save full response to DB
        complete_response = "".join(full_response)
        await save_message(chat_id, "assistant", complete_response)
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )