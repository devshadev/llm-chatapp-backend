# import redis.asyncio as redis
# from app.core import REDIS_HOST, REDIS_PORT

# redis_client = None

# async def connect_redis():
#     global redis_client
#     redis_client = redis.Redis(
#         host=REDIS_HOST,
#         port=REDIS_PORT,
#         decode_responses=True  # returns strings instead of bytes
#     )
#     await redis_client.ping()
#     print("✅ Connected to Redis")

# async def close_redis():
#     global redis_client
#     if redis_client:
#         await redis_client.close()
#         print("❌ Redis connection closed")

# def get_redis():
#     return redis_client


import redis.asyncio as redis
from app.core import REDIS_URL  # ← change this import

redis_client = None

async def connect_redis():
    global redis_client
    redis_client = await redis.from_url(
        REDIS_URL,
        decode_responses=True,
        ssl_cert_reqs=None  # required for Upstash TLS
    )
    await redis_client.ping()
    print("✅ Connected to Redis")

async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        print("❌ Redis connection closed")

def get_redis():
    return redis_client