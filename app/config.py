"""Application configuration using Pydantic Settings.

All secrets and environment-specific values are read from environment
variables (or a .env file). Nothing is hardcoded.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram
    bot_token: str
    admin_ids: str = ""
    storage_channel_id: int

    # Infrastructure
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/movie_bot"
    redis_url: str = "redis://redis:6379/0"

    # Runtime
    log_level: str = "INFO"
    environment: str = "production"

    # Webhook (used when USE_WEBHOOK=true)
    use_webhook: bool = False
    webhook_url: str = ""  # e.g. https://your-app.up.railway.app/webhook/bot
    webhook_path: str = "/webhook/bot"
    webhook_host: str = "0.0.0.0"
    # Railway injects a PORT env var; default to it so the proxy can reach us.
    webhook_port: int = 8000
    webhook_secret: str = ""  # optional secret token for webhook
    # Railway/Heroku-style port override (takes precedence over webhook_port).
    port: int | None = None

    @property
    def effective_webhook_port(self) -> int:
        """Return the port the webhook server should bind to.

        Prefers the platform-injected PORT (Railway/Heroku), falling back to
        webhook_port.
        """
        return self.port or self.webhook_port

    # Behavioural knobs
    subscription_cache_ttl: int = 300  # seconds
    pending_movie_ttl: int = 600  # seconds (10 minutes)
    rate_limit_requests: int = 10
    rate_limit_window: int = 60  # seconds
    broadcast_batch_size: int = 20
    broadcast_delay: float = 0.05  # seconds between batches

    @field_validator("admin_ids")
    @classmethod
    def _parse_admin_ids(cls, value: str) -> str:
        return value.strip()

    @property
    def admin_id_list(self) -> list[int]:
        """Return the list of admin Telegram IDs."""
        if not self.admin_ids:
            return []
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]

    def is_admin(self, telegram_id: int) -> bool:
        """Return True if the given Telegram ID is an admin."""
        return telegram_id in self.admin_id_list


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
