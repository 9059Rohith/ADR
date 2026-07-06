"""SentinelArena API Gateway — Application Configuration.

Centralizes all configuration via environment variables with Pydantic Settings.
Supports .env file loading for development.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All secrets and configuration are loaded from environment variables,
    never hardcoded. See .env.example for documentation of each variable.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Database ---
    database_url: str = (
        "postgresql+asyncpg://sentinel:sentinel_dev@localhost:5432/sentinel_arena"
    )

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Auth ---
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # --- Anthropic ---
    anthropic_api_key: str = ""
    anthropic_fast_model: str = "claude-sonnet-4-20250514"
    anthropic_reasoning_model: str = "claude-sonnet-4-20250514"

    # --- Weather ---
    weather_api_key: str = ""
    weather_api_base_url: str = "https://api.openweathermap.org/data/2.5"

    # --- Application ---
    api_gateway_port: int = 8000
    allowed_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002"
    log_level: Literal["debug", "info", "warning", "error", "critical"] = "info"
    log_format: Literal["json", "console"] = "json"

    # --- Rate Limiting ---
    rate_limit_requests_per_minute: int = 60
    rate_limit_llm_requests_per_minute: int = 20

    # --- Crowd Simulator ---
    simulator_interval_ms: int = 5000
    simulator_num_zones: int = 12
    simulator_max_capacity_per_zone: int = 500

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def use_real_llm(self) -> bool:
        """Check if a real LLM API key is configured."""
        return bool(self.anthropic_api_key)

    @property
    def use_real_weather(self) -> bool:
        """Check if a real weather API key is configured."""
        return bool(self.weather_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings singleton."""
    return Settings()
