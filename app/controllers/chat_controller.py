from fastapi import APIRouter, HTTPException, Depends
from app.core.dependencies import get_current_user
from app.models.chat import CreateChatRequest, SendMessageRequest
from app.services.chat_service import (
    create_chat,
    get_user_chats,
    get_chat_with_messages,
    update_chat_title,
    delete_chat,
    get_chat_messages,
    send_message_and_respond,
    stream_message_response
)

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/")
async def create_new_chat(body: CreateChatRequest, current_user=Depends(get_current_user)):
    chat = await create_chat(current_user["id"], body.title)
    return {
        "id": chat["id"],
        "title": chat["title"],
        "created_at": chat["created_at"],
        "updated_at": chat["updated_at"]
    }


@router.get("/")
async def get_chats(current_user=Depends(get_current_user)):
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


@router.get("/{chat_id}")
async def get_single_chat(chat_id: str, current_user=Depends(get_current_user)):
    chat, messages = await get_chat_with_messages(chat_id, current_user["id"])
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
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


@router.patch("/{chat_id}")
async def update_title(chat_id: str, body: CreateChatRequest, current_user=Depends(get_current_user)):
    updated = await update_chat_title(chat_id, current_user["id"], body.title)
    if not updated:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Title updated"}


@router.delete("/{chat_id}")
async def delete_single_chat(chat_id: str, current_user=Depends(get_current_user)):
    deleted = await delete_chat(chat_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat deleted"}


@router.get("/{chat_id}/messages")
async def get_messages(chat_id: str, current_user=Depends(get_current_user)):
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


@router.post("/{chat_id}/messages")
async def send_message(chat_id: str, body: SendMessageRequest, current_user=Depends(get_current_user)):
    user_message, assistant_message, error = await send_message_and_respond(
        chat_id, current_user["id"], body.content
    )
    if error:
        raise HTTPException(status_code=404, detail=error)
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
async def send_message_stream(chat_id: str, body: SendMessageRequest, current_user=Depends(get_current_user)):
    response = await stream_message_response(chat_id, current_user["id"], body.content)
    if response is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return response