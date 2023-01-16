from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, Field, PostgresDsn, SecretStr, validator


class AsyncPostgresDsn(PostgresDsn):
    allowed_schemes = {"postgres+asyncpg", "postgresql+asyncpg"}


class Config(BaseSettings):
    TELEGRAM_TOKEN: str

    # Host for webhook and webserver. Should be accessible from the Internet for Telegram to work.
    HOST: str = "https://bot.mirea.ninja"
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

    MIREA_NINJA_GROUP_ID: int = Field(default=-567317308, env="MIREA_NINJA_GROUP_ID")

    # Yandex
    YANDEX_API_KEY: SecretStr
    YANDEX_WEATHER_API_KEY: SecretStr
    YANDEX_FOLDER_ID: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings():
    return Config()
