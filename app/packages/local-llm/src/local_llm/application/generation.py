from __future__ import annotations

import asyncio
import json
import logging
import threading
from collections.abc import AsyncIterator

from local_llm.adapters.errors import (
    CapacityError,
    GenerationTimeoutError,
    InferenceError,
    ModelNotFoundError,
)
from local_llm.config import Settings
from local_llm.core.contracts import (
    GenerationParameters,
    InferenceProvider,
    ModelStatus,
    ProviderChunk,
    ProviderResult,
    Readiness,
)
from local_llm.core.performance import GenerationMeasurement
from local_llm.interfaces.http.schemas import GenerationRequest, GenerationResponse


class InvalidRequestError(InferenceError):
    code = "invalid_request"
    status_code = 400
    public_message = "A solicitação excede um limite configurado."


class GenerationService:
    def __init__(self, settings: Settings, provider: InferenceProvider) -> None:
        self.settings = settings
        self.provider = provider
        self._sync_slots = threading.BoundedSemaphore(settings.max_concurrency)
        self._async_slots = asyncio.Semaphore(settings.max_concurrency)
        self._logger = logging.getLogger("uvicorn.error")
        self._logger.setLevel(logging.INFO)

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
        measurement = self._measurement(parameters.model_name, request_id, streaming=False)
        if not self._sync_slots.acquire(blocking=False):
            self._finish_measurement(measurement, None, "capacity")
            raise CapacityError()
        try:
            result = self.provider.generate_sync(parameters, request_id)
        except Exception as exc:
            self._finish_measurement(measurement, None, self._outcome(exc))
            raise
        finally:
            self._sync_slots.release()
        self._finish_measurement(measurement, result.usage, "success")
        return self._response(result, request_id)

    async def generate_async(
        self, request: GenerationRequest, request_id: str
    ) -> GenerationResponse:
        parameters = self.parameters(request)
        measurement = self._measurement(parameters.model_name, request_id, streaming=False)
        if self._async_slots.locked():
            self._finish_measurement(measurement, None, "capacity")
            raise CapacityError()
        await self._async_slots.acquire()
        try:
            result = await self.provider.generate_async(parameters, request_id)
        except Exception as exc:
            self._finish_measurement(measurement, None, self._outcome(exc))
            raise
        finally:
            self._async_slots.release()
        self._finish_measurement(measurement, result.usage, "success")
        return self._response(result, request_id)

    async def stream(
        self, request: GenerationRequest, request_id: str
    ) -> AsyncIterator[ProviderChunk]:
        parameters = self.parameters(request)
        measurement = self._measurement(parameters.model_name, request_id, streaming=True)
        if self._async_slots.locked():
            self._finish_measurement(measurement, None, "capacity")
            raise CapacityError()
        await self._async_slots.acquire()
        usage = None
        outcome = "success"
        try:
            async for chunk in self.provider.stream(parameters, request_id):
                if chunk.text:
                    measurement.observe_first_token()
                if chunk.usage is not None:
                    usage = chunk.usage
                yield chunk
        except Exception as exc:
            outcome = self._outcome(exc)
            raise
        finally:
            self._async_slots.release()
            self._finish_measurement(measurement, usage, outcome)

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

    def _measurement(
        self, model: str, request_id: str, *, streaming: bool
    ) -> GenerationMeasurement:
        return GenerationMeasurement(
            model=model,
            streaming=streaming,
            max_concurrency=self.settings.max_concurrency,
            profile=self.settings.performance_profile,
            request_id=request_id,
        )

    def _finish_measurement(
        self,
        measurement: GenerationMeasurement,
        usage: dict[str, object] | None,
        outcome: str,
    ) -> None:
        measurement.finish(usage=usage, outcome=outcome)
        self._logger.info("generation_performance %s", json.dumps(measurement.as_dict()))

    @staticmethod
    def _outcome(error: Exception) -> str:
        if isinstance(error, CapacityError):
            return "capacity"
        if isinstance(error, GenerationTimeoutError):
            return "timeout"
        return "inference_error"
