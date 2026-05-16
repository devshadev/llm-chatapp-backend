from datetime import datetime
from bson import ObjectId
from fastapi.responses import StreamingResponse
import json

from app.core.database import get_db
from app.core.redis import get_redis

CACHE_TTL = 60 * 30  # 30 minutes


# ─── Serializer ───────────────────────────────────────────────────────────────

def serialize_message(msg):
    return {
        "id": str(msg.get("_id", msg.get("id", ""))),
        "chat_id": msg.get("chat_id"),
        "role": msg.get("role"),
        "content": msg.get("content"),
        "created_at": (
            msg["created_at"].isoformat()
            if hasattr(msg.get("created_at"), "isoformat")
            else str(msg.get("created_at"))
        )
    }


# ─── Cache helpers ─────────────────────────────────────────────────────────────

async def get_cached_messages(chat_id: str):
    redis = get_redis()
    cached = await redis.get(f"chat_messages:{chat_id}")
    if cached:
        print(f"✅ Cache HIT for chat {chat_id}")
        return json.loads(cached)
    print(f"❌ Cache MISS for chat {chat_id}")
    return None


async def set_cached_messages(chat_id: str, messages: list):
    redis = get_redis()
    await redis.setex(f"chat_messages:{chat_id}", CACHE_TTL, json.dumps(messages))


async def invalidate_cache(chat_id: str):
    redis = get_redis()
    await redis.delete(f"chat_messages:{chat_id}")
    print(f"🗑️ Cache invalidated for chat {chat_id}")


# ─── Core CRUD ─────────────────────────────────────────────────────────────────

async def create_chat(user_id: str, title: str = "New Chat") -> dict:
    db = get_db()
    chat_doc = {
        "user_id": user_id,
        "title": title,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await db.chats.insert_one(chat_doc)
    chat_doc["id"] = str(result.inserted_id)
    return chat_doc


async def get_user_chats(user_id: str) -> list:
    db = get_db()
    cursor = db.chats.find({"user_id": user_id}).sort("updated_at", -1)
    chats = []
    async for chat in cursor:
        chat["id"] = str(chat["_id"])
        chats.append(chat)
    return chats


async def get_chat(chat_id: str, user_id: str) -> dict:
    db = get_db()
    chat = await db.chats.find_one({
        "_id": ObjectId(chat_id),
        "user_id": user_id
    })
    if chat:
        chat["id"] = str(chat["_id"])
    return chat


async def delete_chat(chat_id: str, user_id: str) -> bool:
    db = get_db()
    result = await db.chats.delete_one({
        "_id": ObjectId(chat_id),
        "user_id": user_id
    })
    if result.deleted_count:
        await db.messages.delete_many({"chat_id": chat_id})
        await invalidate_cache(chat_id)
        return True
    return False


async def save_message(chat_id: str, role: str, content: str) -> dict:
    db = get_db()
    message_doc = {
        "chat_id": chat_id,
        "role": role,
        "content": content,
        "created_at": datetime.utcnow()
    }
    result = await db.messages.insert_one(message_doc)
    message_doc["id"] = str(result.inserted_id)
    await db.chats.update_one(
        {"_id": ObjectId(chat_id)},
        {"$set": {"updated_at": datetime.utcnow()}}
    )
    await invalidate_cache(chat_id)
    return message_doc


async def get_chat_messages(chat_id: str, user_id: str):
    db = get_db()
    chat = await get_chat(chat_id, user_id)
    if not chat:
        return None

    cached = await get_cached_messages(chat_id)
    if cached is not None:
        return cached

    cursor = db.messages.find({"chat_id": chat_id}).sort("created_at", 1)
    messages = []
    async for message in cursor:
        messages.append(serialize_message(message))

    await set_cached_messages(chat_id, messages)
    return messages


async def update_chat_title(chat_id: str, user_id: str, title: str) -> bool:
    db = get_db()
    result = await db.chats.update_one(
        {"_id": ObjectId(chat_id), "user_id": user_id},
        {"$set": {"title": title, "updated_at": datetime.utcnow()}}
    )
    return result.modified_count > 0


# ─── Composed service functions (called directly by controller) ────────────────

async def get_chat_with_messages(chat_id: str, user_id: str):
    """Single call that returns chat + messages together. Used by GET /chats/{id}"""
    chat = await get_chat(chat_id, user_id)
    if not chat:
        return None, None

    messages = await get_chat_messages(chat_id, user_id)
    return chat, messages


async def send_message_and_respond(chat_id: str, user_id: str, content: str):
    """Verify ownership, save user msg, call LLM, save assistant msg. Used by POST /chats/{id}/messages"""
    from app.services.llm_service import get_llm_response

    chat = await get_chat(chat_id, user_id)
    if not chat:
        return None, None, "Chat not found"

    user_message = await save_message(chat_id, "user", content)
    llm_reply = await get_llm_response(content)
    assistant_message = await save_message(chat_id, "assistant", llm_reply)

    return user_message, assistant_message, None


async def stream_message_response(chat_id: str, user_id: str, content: str):
    """Verify ownership, save user msg, stream LLM tokens, save full response. Used by POST /chats/{id}/messages/stream"""
    from app.services.llm_service import stream_llm_response

    chat = await get_chat(chat_id, user_id)
    if not chat:
        return None

    await save_message(chat_id, "user", content)

    full_response = []

    async def generate():
        async for token in stream_llm_response(content):
            full_response.append(token)
            yield f"data: {json.dumps({'token': token})}\n\n"

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