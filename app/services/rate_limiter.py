"""Rate limiting service backed by Redis."""

import logging

from app.config import settings
from app.services.redis_service import redis_client

logger = logging.getLogger(__name__)

RATE_LIMIT_PREFIX = "rate_limit:"


class RateLimiter:
    """Simple fixed-window rate limiter."""

    async def check(self, key: str, limit: int | None = None) -> bool:
        """Return True if the action is allowed, False if rate-limited."""
        limit = limit or settings.rate_limit_requests
        redis_key = f"{RATE_LIMIT_PREFIX}{key}"
        try:
            count = await redis_client.incr(redis_key)
            if count == 1:
                await redis_client.expire(redis_key, settings.rate_limit_window)
            return count <= limit
        except Exception as exc:  # noqa: BLE001
            # Fail open if Redis is unavailable to avoid blocking users.
            logger.warning("Rate limiter error: %s", exc)
            return True
