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
    id: str | None = None
    object: Literal["model"] = "model"
    owned_by: str = "local-llm"
    model: str
    status: Literal["ready", "unavailable"]
    default: bool
    reason: str | None = None


class ModelListResponse(BaseModel):
    data: list[ModelStatusResponse]
    object: Literal["list"] = "list"


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=100_000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content deve conter pelo menos um caractere não branco")
        return value


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str | None = Field(default=None, min_length=1, max_length=128)
    messages: list[ChatMessage] = Field(min_length=1, max_length=128)
    max_tokens: int | None = Field(default=None, ge=1, le=4096)
    temperature: float | None = Field(default=None, ge=0, le=2)
    stream: bool = False


class ChatChoiceMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatChoiceMessage
    finish_reason: str = "stop"


class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: dict[str, Any] | None = None


class ChatChunkDelta(BaseModel):
    role: Literal["assistant"] | None = None
    content: str | None = None


class ChatCompletionChunkChoice(BaseModel):
    index: int = 0
    delta: ChatChunkDelta
    finish_reason: str | None = None


class ChatCompletionChunk(BaseModel):
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: list[ChatCompletionChunkChoice]
    usage: dict[str, Any] | None = None


class BenchmarkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str | None = Field(default=None, min_length=1, max_length=128)
    prompt_tokens: int = Field(default=32, ge=1, le=4096)
    output_tokens: int = Field(default=32, ge=1, le=512)
    concurrency: int = Field(default=1, ge=1, le=32)
    max_requests: int = Field(default=1, ge=1, le=1000)
    max_duration_seconds: int = Field(default=0, ge=0, le=3600)


class BenchmarkResponse(BaseModel):
    run_id: str
    model: str
    status: Literal["running", "completed", "failed"]
    results_path: str
    files: list[str] = Field(default_factory=list)
    successful_requests: int | None = None
    errored_requests: int | None = None
    error: str | None = None
