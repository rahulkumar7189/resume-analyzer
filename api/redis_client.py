import os
import json
import redis

# Use the REDIS_URL from env or fallback to localhost
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    redis_conn = redis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    print(f"[redis] Connection failed: {e}")
    redis_conn = None

def get_cached_result(cache_key: str):
    if not redis_conn:
        return None
    try:
        data = redis_conn.get(cache_key)
        if data:
            return json.loads(data)
    except Exception as e:
        print(f"[redis] Get error: {e}")
    return None

def set_cached_result(cache_key: str, data: dict, ttl: int = 3600):
    if not redis_conn:
        return
    try:
        redis_conn.setex(cache_key, ttl, json.dumps(data))
    except Exception as e:
        print(f"[redis] Set error: {e}")
