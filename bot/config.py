from functools import lru_cache
from typing import Optional

from pydantic import AnyHttpUrl, BaseSettings, Field, PostgresDsn, SecretStr, validator


class AsyncPostgresDsn(PostgresDsn):
    allowed_schemes = {"postgres+asyncpg", "postgresql+asyncpg"}


def _parse_allowed_chats(allowed_chats: str) -> list[int]:
    if isinstance(allowed_chats, int):
        return [allowed_chats]
    return [int(chat) for chat in allowed_chats.split(",")]


class Config(BaseSettings):
    TELEGRAM_TOKEN: str

    RUN_WITH_WEBHOOK: bool = Field(default=False)

    # Host for webhook and webserver. Should be accessible from the Internet for Telegram to work.
    BOT_URL: str = "https://bot.mirea.ninja"
    HOST: str = "bot.mirea.ninja"
    PORT: int = 8000

    # Postgres
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB: str

    POSTGRES_URI: Optional[AsyncPostgresDsn]

    @validator("POSTGRES_URI", pre=True)
    def assemble_db_connection(cls, v, values):
        if isinstance(v, str):
            return v
        return AsyncPostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD").get_secret_value(),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    ALLOWED_CHATS: Optional[list[int]]

    @validator("ALLOWED_CHATS", pre=True)
    def parse_allowed_chats(cls, v):
        return v if isinstance(v, list) else _parse_allowed_chats(v)

    # Yandex
    YANDEX_API_KEY: SecretStr
    YANDEX_WEATHER_API_KEY: SecretStr
    YANDEX_FOLDER_ID: str

    # Discourse
    DISCOURSE_API_KEY: SecretStr
    DISCOURSE_URL: AnyHttpUrl

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings():
    return Config()
