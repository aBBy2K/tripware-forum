from core.redis_conf import redis
from fastapi import HTTPException

async def rate_limit(key, limit):
    count = await redis.incr(f"rate_limit:{key}")

    if count == 1:
        await redis.expire(f"rate_limit:{key}", 60)

    if count > limit:
        raise HTTPException(
            status_code=429,
            detail="too many requests"
        )