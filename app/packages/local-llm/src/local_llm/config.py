from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass(frozen=True)
class ModelDefinition:
    alias: str
    servable_name: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    provider: Literal["ovms"] = Field(default="ovms")
    ovms_url: str = Field(default="http://ovms:8000", min_length=1)
    ovms_default_model: str = Field(default="qwen3-1.7b", min_length=1)
    ovms_model_names: str = Field(
        default="qwen3-1.7b=qwen3-1.7b,qwen3-8b=qwen3-8b",
        min_length=1,
    )
    benchmark_runner_url: str = Field(default="http://benchmark-runner:8080", min_length=1)
    benchmark_default_model: str = Field(default="qwen3-8b", min_length=1, max_length=128)
    benchmark_timeout_seconds: float = Field(default=15.0, gt=0, le=120)
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
        self.model_definitions()
        return self

    def model_definitions(self) -> tuple[ModelDefinition, ...]:
        definitions: list[ModelDefinition] = []
        aliases: set[str] = set()
        servable_names: set[str] = set()
        for item in self.ovms_model_names.split(","):
            alias, separator, servable_name = item.strip().partition("=")
            if not separator:
                alias = servable_name = alias
            if not alias or not servable_name:
                raise ValueError("OVMS_MODEL_NAMES contém uma definição vazia")
            if alias in aliases or servable_name in servable_names:
                raise ValueError("OVMS_MODEL_NAMES não pode conter duplicidades")
            aliases.add(alias)
            servable_names.add(servable_name)
            definitions.append(ModelDefinition(alias, servable_name))
        if self.ovms_default_model not in aliases:
            raise ValueError("OVMS_DEFAULT_MODEL deve existir em OVMS_MODEL_NAMES")
        return tuple(definitions)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
