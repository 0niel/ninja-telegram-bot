from functools import lru_cache
from typing import Optional

from pydantic import AnyHttpUrl
from pydantic import BaseSettings
from pydantic import Field
from pydantic import PostgresDsn
from pydantic import validator


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

    SUPABASE_URL: AnyHttpUrl
    SUPABASE_KEY: str
    SUPABASE_USERNAME: str
    SUPABASE_PASSWORD: str

    ALLOWED_CHATS: Optional[list[int]]

    @validator("ALLOWED_CHATS", pre=True)
    def parse_allowed_chats(cls, v):
        return v if isinstance(v, list) else _parse_allowed_chats(v)

    # Yandex
    YANDEX_API_KEY: str
    YANDEX_WEATHER_API_KEY: str
    YANDEX_FOLDER_ID: str

    # Discourse
    DISCOURSE_API_KEY: str
    DISCOURSE_URL: AnyHttpUrl

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings():
    return Config()
