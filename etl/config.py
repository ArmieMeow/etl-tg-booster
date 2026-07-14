from __future__ import annotations

import logging
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    tg_booster_api_token: str = Field(default="", alias="TG_BOOSTER_API_TOKEN")
    tg_booster_api_base_url: str = Field(default="", alias="TG_BOOSTER_API_BASE_URL")
    tg_booster_account_id: str = Field(default="", alias="TG_BOOSTER_ACCOUNT_ID")
    database_url: str = Field(default="", alias="DATABASE_URL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("tg_booster_api_base_url")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    def validate_for_run(self) -> None:
        missing: list[str] = []
        if not self.tg_booster_api_token:
            missing.append("TG_BOOSTER_API_TOKEN")
        if not self.tg_booster_api_base_url:
            missing.append("TG_BOOSTER_API_BASE_URL")
        if not self.database_url:
            missing.append("DATABASE_URL")
        if missing:
            raise ValueError(f"Missing required env vars: {', '.join(missing)}")

    def validate_for_config_check(self) -> None:
        """Lighter check: DB required; API vars needed only for extract/run."""
        if not self.database_url:
            raise ValueError("Missing required env var: DATABASE_URL")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def setup_logging(level: str | None = None) -> None:
    log_level = (level or get_settings().log_level).upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
