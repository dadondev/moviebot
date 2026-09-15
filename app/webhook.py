"""Aiohttp webhook server for the Telegram bot.

Serves the webhook endpoint that Telegram calls with updates, and a health
check endpoint for Railway.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from aiohttp import web

from app.config import settings

logger = logging.getLogger(__name__)


async def _handle_update(request: web.Request) -> web.Response:
    """Handle an incoming Telegram update."""
    bot: Bot = request.app["bot"]
    dp: Dispatcher = request.app["dispatcher"]

    # Optional secret token check (matches Telegram's secret_token).
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if settings.webhook_secret and secret != settings.webhook_secret:
        return web.Response(status=403)

    try:
        update = Update.model_validate(await request.json())
    except Exception:  # noqa: BLE001
        logger.warning("Invalid update payload")
        return web.Response(status=400)

    await dp.feed_update(bot, update)
    return web.Response(status=200)


async def _health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


def create_app(bot: Bot, dispatcher: Dispatcher) -> web.Application:
    """Build the aiohttp application with webhook routes."""
    app = web.Application()
    app["bot"] = bot
    app["dispatcher"] = dispatcher
    app.router.add_post(settings.webhook_path, _handle_update)
    app.router.add_get("/health", _health)
    return app


async def run_webhook(bot: Bot, dispatcher: Dispatcher) -> None:
    """Set the webhook and start the aiohttp server."""
    if not settings.webhook_url:
        raise ValueError("WEBHOOK_URL is required when USE_WEBHOOK=true")

    # Set the webhook on Telegram.
    await bot.set_webhook(
        url=settings.webhook_url,
        secret_token=settings.webhook_secret or None,
        drop_pending_updates=True,
    )
    logger.info("Webhook set to %s", settings.webhook_url)

    app = create_app(bot, dispatcher)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.webhook_host, settings.webhook_port)
    await site.start()
    logger.info(
        "Webhook server listening on %s:%s%s",
        settings.webhook_host,
        settings.webhook_port,
        settings.webhook_path,
    )

    # Keep running until interrupted.
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
