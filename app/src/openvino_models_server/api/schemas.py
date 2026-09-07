from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str | None = Field(default=None, min_length=1, max_length=128)
    text: str = Field(min_length=1, max_length=100_000)
    max_tokens: int | None = Field(default=None, ge=1, le=4096)
    temperature: float | None = Field(default=None, ge=0, le=2)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text deve conter pelo menos um caractere não branco")
        return value


class GenerationResponse(BaseModel):
    request_id: str
    model: str
    text: str
    finish_reason: str
    usage: dict[str, Any] | None = None


class ErrorDetails(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetails


class HealthResponse(BaseModel):
    status: Literal["alive"]


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    reason: str | None = None


class ModelStatusResponse(BaseModel):
    model: str
    status: Literal["ready", "unavailable"]
    default: bool
    reason: str | None = None


class ModelListResponse(BaseModel):
    data: list[ModelStatusResponse]
    object: Literal["list"] = "list"
