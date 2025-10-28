import redis
from config import REDIS_URL

# Redis client for session management and caching
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def get_redis():
    return redis_client
