from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class GenerationParameters:
    text: str
    max_tokens: int
    temperature: float
    model_name: str = ""


@dataclass(frozen=True)
class ProviderResult:
    model: str
    text: str
    finish_reason: str
    usage: dict[str, Any] | None = None


@dataclass(frozen=True)
class ProviderChunk:
    text: str = ""
    finish_reason: str | None = None
    usage: dict[str, Any] | None = None
    done: bool = False


@dataclass(frozen=True)
class Readiness:
    ready: bool
    reason: str | None = None


@dataclass(frozen=True)
class ModelStatus:
    model_name: str
    ready: bool
    reason: str | None = None


class InferenceProvider(Protocol):
    default_model: str
    model_names: tuple[str, ...]

    def generate_sync(
        self, parameters: GenerationParameters, request_id: str
    ) -> ProviderResult: ...

    async def generate_async(
        self, parameters: GenerationParameters, request_id: str
    ) -> ProviderResult: ...

    def stream(
        self, parameters: GenerationParameters, request_id: str
    ) -> AsyncIterator[ProviderChunk]: ...

    async def readiness(self) -> Readiness: ...

    async def model_statuses(self) -> tuple[ModelStatus, ...]: ...
