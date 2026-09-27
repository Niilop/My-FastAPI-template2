import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "FastAPI Template"
    debug: bool = False
    database_url: str
    secret_key: SecretStr
    access_token_expire_minutes: int = Field(default=30, ge=1)
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret(cls, value: SecretStr) -> SecretStr:
        secret = value.get_secret_value()
        if len(secret.encode()) < 32 or secret.lower().startswith(
            ("change", "your-secret", "replace")
        ):
            raise ValueError("SECRET_KEY must be a randomly generated secret of at least 32 bytes")
        return value

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return (
                json.loads(value)
                if value.strip().startswith("[")
                else [origin.strip() for origin in value.split(",") if origin.strip()]
            )
        return value

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: list[str]) -> list[str]:
        if "*" in value:
            raise ValueError("Use explicit CORS origins when allowing credentials")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
