from motor.motor_asyncio import AsyncIOMotorClient
from app.core import MONGODB_URL, DATABASE_NAME

client = None
db = None

async def connect_db():
    global client, db
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    print("✅ Connected to MongoDB")

async def close_db():
    global client
    if client:
        client.close()
        print("❌ MongoDB connection closed")

def get_db():
    return db