"""Application entry point.

Sets up the bot, registers handlers, middlewares and starts polling.
"""


from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from app.bot.handlers import (
    cancel,
    favorites,
    genres,
    movie,
    rating,
    requests,
    search,
    start,
    subscription,
)
from app.bot.handlers.admin import (
    broadcast,
    channels,
)
from app.bot.handlers.admin import (
    genres as admin_genres,
)
from app.bot.handlers.admin import (
    main as admin_main,
)
from app.bot.handlers.admin import (
    movies as admin_movies,
)
from app.bot.handlers.admin import (
    users as admin_users,
)
from app.bot.middlewares.rate_limit import RateLimitMiddleware
from app.bot.middlewares.registration import UserRegistrationMiddleware
from app.config import settings
from app.logging import get_logger, setup_logging
from app.services.rate_limiter import RateLimiter
from app.services.redis_service import close_redis, redis_client

logger = get_logger(__name__)


def create_bot() -> Bot:
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    storage = RedisStorage(redis_client)
    dp = Dispatcher(storage=storage)

    # Middlewares
    dp.message.middleware(UserRegistrationMiddleware())
    dp.callback_query.middleware(UserRegistrationMiddleware())
    dp.message.middleware(RateLimitMiddleware(RateLimiter()))
    dp.callback_query.middleware(RateLimitMiddleware(RateLimiter()))

    # Routers
    dp.include_router(start.router)
    dp.include_router(cancel.router)
    dp.include_router(movie.router)
    dp.include_router(search.router)
    dp.include_router(genres.router)
    dp.include_router(favorites.router)
    dp.include_router(rating.router)
    dp.include_router(requests.router)
    dp.include_router(subscription.router)
    dp.include_router(admin_main.router)
    dp.include_router(admin_movies.router)
    dp.include_router(channels.router)
    dp.include_router(admin_genres.router)
    dp.include_router(admin_users.router)
    dp.include_router(broadcast.router)

    return dp


async def main() -> None:
    setup_logging()
    logger.info("Starting bot in %s environment", settings.environment)

    bot = create_bot()
    dp = create_dispatcher()

    try:
        if settings.use_webhook:
            from app.webhook import run_webhook

            await run_webhook(bot, dp)
        else:
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)
    finally:
        await close_redis()
        await bot.session.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
