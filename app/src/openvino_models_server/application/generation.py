from __future__ import annotations

import asyncio
import threading
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol

from openvino_models_server.api.schemas import GenerationRequest, GenerationResponse
from openvino_models_server.config import Settings
from openvino_models_server.infrastructure.errors import (
    CapacityError,
    InferenceError,
    ModelNotFoundError,
)


class InvalidRequestError(InferenceError):
    code = "invalid_request"
    status_code = 400
    public_message = "A solicitação excede um limite configurado."


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


class GenerationService:
    def __init__(self, settings: Settings, provider: InferenceProvider) -> None:
        self.settings = settings
        self.provider = provider
        self._sync_slots = threading.BoundedSemaphore(settings.max_concurrency)
        self._async_slots = asyncio.Semaphore(settings.max_concurrency)

    def parameters(self, request: GenerationRequest) -> GenerationParameters:
        if len(request.text) > self.settings.max_input_chars:
            raise InvalidRequestError()
        model_name = self.resolve_model(request)
        max_tokens = request.max_tokens or self.settings.default_max_tokens
        if max_tokens > self.settings.max_tokens_limit:
            raise InvalidRequestError()
        temperature = (
            request.temperature
            if request.temperature is not None
            else self.settings.default_temperature
        )
        return GenerationParameters(request.text, max_tokens, temperature, model_name)

    def resolve_model(self, request: GenerationRequest) -> str:
        model_name = request.model or self.provider.default_model
        if model_name not in self.provider.model_names:
            raise ModelNotFoundError()
        return model_name

    def generate_sync(self, request: GenerationRequest, request_id: str) -> GenerationResponse:
        parameters = self.parameters(request)
        if not self._sync_slots.acquire(blocking=False):
            raise CapacityError()
        try:
            result = self.provider.generate_sync(parameters, request_id)
        finally:
            self._sync_slots.release()
        return self._response(result, request_id)

    async def generate_async(
        self, request: GenerationRequest, request_id: str
    ) -> GenerationResponse:
        parameters = self.parameters(request)
        if self._async_slots.locked():
            raise CapacityError()
        await self._async_slots.acquire()
        try:
            result = await self.provider.generate_async(parameters, request_id)
        finally:
            self._async_slots.release()
        return self._response(result, request_id)

    async def stream(
        self, request: GenerationRequest, request_id: str
    ) -> AsyncIterator[ProviderChunk]:
        parameters = self.parameters(request)
        if self._async_slots.locked():
            raise CapacityError()
        await self._async_slots.acquire()
        try:
            async for chunk in self.provider.stream(parameters, request_id):
                yield chunk
        finally:
            self._async_slots.release()

    async def readiness(self) -> Readiness:
        return await self.provider.readiness()

    async def model_statuses(self) -> tuple[ModelStatus, ...]:
        return await self.provider.model_statuses()

    def _response(self, result: ProviderResult, request_id: str) -> GenerationResponse:
        return GenerationResponse(
            request_id=request_id,
            model=result.model,
            text=result.text,
            finish_reason=result.finish_reason,
            usage=result.usage,
        )
