from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ovms_url: str = Field(default="http://ovms:8000", min_length=1)
    ovms_model_name: str = Field(default="Qwen3-1.7B-int4-ov", min_length=1)
    request_timeout_seconds: float = Field(default=60.0, gt=0, le=600)
    connect_timeout_seconds: float = Field(default=5.0, gt=0, le=60)
    max_input_chars: int = Field(default=12_000, gt=0, le=100_000)
    default_max_tokens: int = Field(default=128, gt=0, le=512)
    max_tokens_limit: int = Field(default=512, gt=0, le=4096)
    default_temperature: float = Field(default=0.2, ge=0, le=2)
    max_concurrency: int = Field(default=2, gt=0, le=32)
    max_sse_event_bytes: int = Field(default=1_000_000, gt=0, le=10_000_000)

    @model_validator(mode="after")
    def validate_generation_defaults(self) -> "Settings":
        if self.default_max_tokens > self.max_tokens_limit:
            raise ValueError("DEFAULT_MAX_TOKENS não pode exceder MAX_TOKENS_LIMIT")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
