"""Quick connectivity check for Telegram + DB + Redis."""

import asyncio

from sqlalchemy import text

from app.database.database import get_engine
from app.main import create_bot
from app.services.redis_service import redis_client


async def main() -> None:
    print("=== Telegram ===")
    bot = create_bot()
    try:
        me = await bot.get_me()
        print("Connected:", me.username)
    except Exception as exc:  # noqa: BLE001
        print("Telegram ERROR:", type(exc).__name__, exc)
    finally:
        await bot.session.close()

    print("=== PostgreSQL ===")
    try:
        async with get_engine().connect() as conn:
            r = await conn.execute(text("SELECT 1"))
            print("DB OK:", r.scalar())
    except Exception as exc:  # noqa: BLE001
        print("DB ERROR:", type(exc).__name__, exc)

    print("=== Redis ===")
    try:
        print("Redis OK:", await redis_client.ping())
    except Exception as exc:  # noqa: BLE001
        print("Redis ERROR:", type(exc).__name__, exc)


if __name__ == "__main__":
    asyncio.run(main())