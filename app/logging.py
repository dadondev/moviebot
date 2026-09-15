"""Logging configuration.

Never log secrets (BOT_TOKEN, passwords, credentials).
"""

import logging
import sys

from app.config import settings

_LOGGED_SECRETS = {settings.bot_token}


def _sanitize(record: logging.LogRecord) -> logging.LogRecord:
    """Redact known secrets from log messages."""
    msg = record.getMessage()
    for secret in _LOGGED_SECRETS:
        if secret and secret in msg:
            msg = msg.replace(secret, "***")
    record.msg = msg
    record.args = ()
    return record


class _SanitizingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        _sanitize(record)
        return True


def setup_logging() -> None:
    """Configure the root logger with a sanitizing filter."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(_SanitizingFilter())

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    # Keep third-party loggers quieter in production.
    if settings.environment == "production":
        logging.getLogger("aiogram").setLevel(logging.WARNING)
        logging.getLogger("aiohttp").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger."""
    return logging.getLogger(name)
