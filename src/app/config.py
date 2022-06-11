from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings


@lru_cache
def get_settings() -> Settings:
    return Settings()


class Settings(BaseSettings):
    ENV: str
    DEBUG: bool = False
    TESTING: bool = False

    HOST: str = "127.0.0.1"
    PORT: int = 5000

    SQLALCHEMY_DATABASE_URI: str
    SQLALCHEMY_POOL_SIZE: Optional[int] = None
    SQLALCHEMY_MAX_OVERFLOW: Optional[int] = None
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = False
