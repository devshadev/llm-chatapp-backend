# # All chat business logic — like chatService.js in Node.js
# from datetime import datetime
# from bson import ObjectId
# from app.core.database import get_db

# # --- Create a new chat thread ---
# async def create_chat(user_id: str, title: str = "New Chat") -> dict:
#     db = get_db()
#     chat_doc = {
#         "user_id": user_id,
#         "title": title,
#         "created_at": datetime.utcnow(),
#         "updated_at": datetime.utcnow()
#     }
#     result = await db.chats.insert_one(chat_doc)
#     chat_doc["id"] = str(result.inserted_id)
#     return chat_doc

# # --- Get all chats for a user ---
# async def get_user_chats(user_id: str) -> list:
#     db = get_db()
#     # like .find().sort() in Mongoose
#     cursor = db.chats.find(
#         {"user_id": user_id}
#     ).sort("updated_at", -1)  # newest first
#     chats = []
#     async for chat in cursor:
#         chat["id"] = str(chat["_id"])
#         chats.append(chat)
#     return chats

# # --- Get a single chat (and verify ownership) ---
# async def get_chat(chat_id: str, user_id: str) -> dict:
#     db = get_db()
#     chat = await db.chats.find_one({
#         "_id": ObjectId(chat_id),
#         "user_id": user_id  # make sure this chat belongs to this user
#     })
#     if chat:
#         chat["id"] = str(chat["_id"])
#     return chat

# # --- Delete a chat and all its messages ---
# async def delete_chat(chat_id: str, user_id: str) -> bool:
#     db = get_db()
#     result = await db.chats.delete_one({
#         "_id": ObjectId(chat_id),
#         "user_id": user_id
#     })
#     if result.deleted_count:
#         # Also delete all messages in this chat
#         await db.messages.delete_many({"chat_id": chat_id})
#         return True
#     return False

# # --- Save a message to a chat ---
# async def save_message(chat_id: str, role: str, content: str) -> dict:
#     db = get_db()
#     message_doc = {
#         "chat_id": chat_id,
#         "role": role,       # "user" or "assistant"
#         "content": content,
#         "created_at": datetime.utcnow()
#     }
#     result = await db.messages.insert_one(message_doc)
#     message_doc["id"] = str(result.inserted_id)

#     # Update chat's updated_at timestamp
#     await db.chats.update_one(
#         {"_id": ObjectId(chat_id)},
#         {"$set": {"updated_at": datetime.utcnow()}}
#     )
#     return message_doc

# # --- Get all messages in a chat ---
# async def get_chat_messages(chat_id: str, user_id: str) -> list:
#     db = get_db()

#     # First verify the chat belongs to this user
#     chat = await get_chat(chat_id, user_id)
#     if not chat:
#         return None  # chat not found or not owned by user

#     cursor = db.messages.find(
#         {"chat_id": chat_id}
#     ).sort("created_at", 1)  # oldest first

#     messages = []
#     async for message in cursor:
#         message["id"] = str(message["_id"])
#         messages.append(message)
#     return messages

# # --- Update chat title ---
# async def update_chat_title(chat_id: str, user_id: str, title: str) -> bool:
#     db = get_db()
#     result = await db.chats.update_one(
#         {"_id": ObjectId(chat_id), "user_id": user_id},
#         {"$set": {"title": title, "updated_at": datetime.utcnow()}}
#     )
#     return result.modified_count > 0



from datetime import datetime
from bson import ObjectId
import json
from app.core.database import get_db
from app.core.redis import get_redis

CACHE_TTL = 60 * 30  # 30 minutes

# --- Helper: convert MongoDB doc to JSON-serializable dict ---
def serialize_message(msg):
    return {
        "id": str(msg.get("_id", msg.get("id", ""))),
        "chat_id": msg.get("chat_id"),
        "role": msg.get("role"),
        "content": msg.get("content"),
        "created_at": msg["created_at"].isoformat() if hasattr(msg.get("created_at"), "isoformat") else str(msg.get("created_at"))
    }

# --- Cache helpers ---
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
    await redis.setex(
        f"chat_messages:{chat_id}",
        CACHE_TTL,
        json.dumps(messages)
    )

async def invalidate_cache(chat_id: str):
    redis = get_redis()
    await redis.delete(f"chat_messages:{chat_id}")
    print(f"🗑️ Cache invalidated for chat {chat_id}")

# --- Create a new chat thread ---
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

# --- Get all chats for a user ---
async def get_user_chats(user_id: str) -> list:
    db = get_db()
    cursor = db.chats.find({"user_id": user_id}).sort("updated_at", -1)
    chats = []
    async for chat in cursor:
        chat["id"] = str(chat["_id"])
        chats.append(chat)
    return chats

# --- Get a single chat ---
async def get_chat(chat_id: str, user_id: str) -> dict:
    db = get_db()
    chat = await db.chats.find_one({
        "_id": ObjectId(chat_id),
        "user_id": user_id
    })
    if chat:
        chat["id"] = str(chat["_id"])
    return chat

# --- Delete a chat and all its messages ---
async def delete_chat(chat_id: str, user_id: str) -> bool:
    db = get_db()
    result = await db.chats.delete_one({
        "_id": ObjectId(chat_id),
        "user_id": user_id
    })
    if result.deleted_count:
        await db.messages.delete_many({"chat_id": chat_id})
        await invalidate_cache(chat_id)  # 👈 clear cache on delete
        return True
    return False

# --- Save a message ---
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

    # Invalidate cache so next load gets fresh messages
    await invalidate_cache(chat_id)  # 👈 clear cache when new message added
    return message_doc

# --- Get all messages (with caching) ---
async def get_chat_messages(chat_id: str, user_id: str):
    db = get_db()

    # Verify ownership
    chat = await get_chat(chat_id, user_id)
    if not chat:
        return None

    # Try cache first
    cached = await get_cached_messages(chat_id)
    if cached is not None:
        return cached  # return from Redis instantly

    # Cache miss — load from MongoDB
    cursor = db.messages.find({"chat_id": chat_id}).sort("created_at", 1)
    messages = []
    async for message in cursor:
        messages.append(serialize_message(message))

    # Save to Redis for next time
    await set_cached_messages(chat_id, messages)
    return messages

# --- Update chat title ---
async def update_chat_title(chat_id: str, user_id: str, title: str) -> bool:
    db = get_db()
    result = await db.chats.update_one(
        {"_id": ObjectId(chat_id), "user_id": user_id},
        {"$set": {"title": title, "updated_at": datetime.utcnow()}}
    )
    return result.modified_count > 0