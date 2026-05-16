from app.core.database import get_db
import pymongo

async def initialize_indexes():
    db = get_db()

    # Users collection indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.users.create_index("github_id", sparse=True)

    # Chats collection indexes
    await db.chats.create_index("user_id")
    await db.chats.create_index([("updated_at", pymongo.DESCENDING)])

    # Messages collection indexes
    await db.messages.create_index("chat_id")
    await db.messages.create_index([("created_at", pymongo.ASCENDING)])

    print("✅ Database indexes initialized")