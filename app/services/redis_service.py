"""Redis client and helper functions.

Used for FSM storage, pending movie codes, subscription cache and rate limiting.
Never store movie bytes here.
"""

import redis.asyncio as aioredis

from app.config import settings

redis_client = aioredis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)


async def ping_redis() -> bool:
    """Return True if Redis is reachable."""
    try:
        return bool(await redis_client.ping())
    except Exception:
        return False


async def close_redis() -> None:
    await redis_client.aclose()
