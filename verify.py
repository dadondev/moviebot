"""Quick verification script: check DB tables and Redis connectivity."""

import asyncio

from sqlalchemy import text

from app.database.database import get_engine
from app.services.redis_service import redis_client


async def main() -> None:
    print("=== PostgreSQL tables ===")
    async with get_engine().connect() as conn:
        result = await conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        )
        tables = [row[0] for row in result.all()]
        print(tables)

        # Check series columns.
        r = await conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='movies' AND column_name='is_series'"
            )
        )
        print("movies.is_series:", r.scalar())
        r2 = await conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='movie_files' AND column_name='episode_number'"
            )
        )
        print("movie_files.episode_number:", r2.scalar())

        # Check user_id column types.
        for table in ("favorites", "ratings", "movie_requests"):
            r3 = await conn.execute(
                text(
                    "SELECT data_type FROM information_schema.columns "
                    f"WHERE table_name='{table}' AND column_name='user_id'"
                )
            )
            print(f"{table}.user_id type:", r3.scalar())

    print("\n=== Redis ping ===")
    try:
        pong = await redis_client.ping()
        print("Redis OK:", pong)
    except Exception as exc:  # noqa: BLE001
        print("Redis error:", exc)

    print("\n=== Telegram bot ===")
    from app.main import create_bot

    bot = create_bot()
    try:
        me = await bot.get_me()
        print("Bot connected:", me.username, "| ID:", me.id)
    except Exception as exc:  # noqa: BLE001
        print("Bot error:", exc)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())