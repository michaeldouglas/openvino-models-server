from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from local_llm.adapters.errors import (
    GenerationTimeoutError,
    UpstreamResponseError,
    UpstreamUnavailableError,
)
from local_llm.config import Settings
from local_llm.core.contracts import (
    GenerationParameters,
    ModelStatus,
    ProviderChunk,
    ProviderResult,
    Readiness,
)


class OVMSClient:
    """OpenAI-compatible OVMS adapter with one reusable client per protocol."""

    def __init__(self, settings: Settings) -> None:
        definitions = settings.model_definitions()
        self.default_model = settings.ovms_default_model
        self.model_names = tuple(definition.alias for definition in definitions)
        self._servable_names = {
            definition.alias: definition.servable_name for definition in definitions
        }
        timeout = httpx.Timeout(
            settings.request_timeout_seconds, connect=settings.connect_timeout_seconds
        )
        limits = httpx.Limits(
            max_connections=settings.max_concurrency,
            max_keepalive_connections=settings.max_concurrency,
        )
        self._max_event_bytes = settings.max_sse_event_bytes
        self._sync_client = httpx.Client(
            base_url=settings.ovms_url.rstrip("/"), timeout=timeout, limits=limits
        )
        self._async_client = httpx.AsyncClient(
            base_url=settings.ovms_url.rstrip("/"), timeout=timeout, limits=limits
        )

    def generate_sync(self, parameters: GenerationParameters, request_id: str) -> ProviderResult:
        try:
            response = self._sync_client.post(
                "/v1/chat/completions", json=self._payload(parameters, request_id, False)
            )
        except httpx.TimeoutException as exc:
            raise GenerationTimeoutError() from exc
        except httpx.HTTPError as exc:
            raise UpstreamUnavailableError() from exc
        return self._parse_result(response, parameters.model_name or self.default_model)

    async def generate_async(
        self, parameters: GenerationParameters, request_id: str
    ) -> ProviderResult:
        try:
            response = await self._async_client.post(
                "/v1/chat/completions", json=self._payload(parameters, request_id, False)
            )
        except httpx.TimeoutException as exc:
            raise GenerationTimeoutError() from exc
        except httpx.HTTPError as exc:
            raise UpstreamUnavailableError() from exc
        return self._parse_result(response, parameters.model_name or self.default_model)

    async def stream(
        self, parameters: GenerationParameters, request_id: str
    ) -> AsyncIterator[ProviderChunk]:
        try:
            async with self._async_client.stream(
                "POST", "/v1/chat/completions", json=self._payload(parameters, request_id, True)
            ) as response:
                if response.status_code >= 400:
                    raise UpstreamResponseError()
                async for chunk in self._iter_sse(
                    response, parameters.model_name or self.default_model
                ):
                    yield chunk
        except GenerationTimeoutError:
            raise
        except UpstreamResponseError:
            raise
        except httpx.TimeoutException as exc:
            raise GenerationTimeoutError() from exc
        except httpx.HTTPError as exc:
            raise UpstreamUnavailableError() from exc

    async def readiness(self) -> Readiness:
        statuses = await self.model_statuses()
        default_status = next(
            (status for status in statuses if status.model_name == self.default_model), None
        )
        if default_status is None:
            return Readiness(False, "model_unavailable")
        return Readiness(default_status.ready, default_status.reason)

    async def model_statuses(self) -> tuple[ModelStatus, ...]:
        try:
            response = await self._async_client.get("/v1/models")
        except httpx.HTTPError:
            return tuple(
                ModelStatus(name, False, "upstream_unavailable") for name in self.model_names
            )
        if response.status_code >= 400:
            return tuple(ModelStatus(name, False, "model_unavailable") for name in self.model_names)
        try:
            body = response.json()
        except ValueError:
            return tuple(ModelStatus(name, False, "upstream_failed") for name in self.model_names)
        models = body.get("data", []) if isinstance(body, dict) else []
        ids = {item.get("id") for item in models if isinstance(item, dict)}
        return tuple(
            ModelStatus(
                name,
                self._servable_names[name] in ids,
                None if self._servable_names[name] in ids else "model_unavailable",
            )
            for name in self.model_names
        )

    async def aclose(self) -> None:
        await self._async_client.aclose()
        self._sync_client.close()

    def close(self) -> None:
        self._sync_client.close()

    def _payload(
        self, parameters: GenerationParameters, request_id: str, stream: bool
    ) -> dict[str, Any]:
        return {
            "model": self._servable_names.get(
                parameters.model_name or self.default_model,
                parameters.model_name or self.default_model,
            ),
            "messages": [{"role": "user", "content": parameters.text}],
            "max_tokens": parameters.max_tokens,
            "temperature": parameters.temperature,
            "chat_template_kwargs": {"enable_thinking": False},
            "stream": stream,
            "user": request_id,
        }

    def _parse_result(self, response: httpx.Response, model_name: str) -> ProviderResult:
        if response.status_code >= 400:
            raise UpstreamResponseError()
        try:
            body = response.json()
            self._validate_response_model(body, model_name)
            choice = body["choices"][0]
            message = choice.get("message", {})
            text = message.get("content", choice.get("text", ""))
            finish_reason = choice.get("finish_reason") or "stop"
            if not isinstance(text, str) or not isinstance(finish_reason, str):
                raise ValueError
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise UpstreamResponseError() from exc
        usage = body.get("usage")
        return ProviderResult(
            model_name,
            text,
            finish_reason,
            usage if isinstance(usage, dict) else None,
        )

    def _validate_response_model(self, body: Any, model_name: str) -> None:
        if not isinstance(body, dict):
            raise UpstreamResponseError()
        upstream_model = body.get("model")
        expected_model = self._servable_names.get(model_name, model_name)
        if upstream_model is not None and upstream_model not in {model_name, expected_model}:
            raise UpstreamResponseError()

    async def _iter_sse(
        self, response: httpx.Response, model_name: str
    ) -> AsyncIterator[ProviderChunk]:
        data_lines: list[str] = []
        current_size = 0
        async for line in response.aiter_lines():
            current_size += len(line.encode("utf-8"))
            if current_size > self._max_event_bytes:
                raise UpstreamResponseError()
            if not line:
                if data_lines:
                    chunk = self._parse_chunk("\n".join(data_lines), model_name)
                    data_lines = []
                    current_size = 0
                    if chunk is not None:
                        yield chunk
                        if chunk.done:
                            return
                continue
            if line.startswith("data:"):
                data_lines.append(line[5:].lstrip())
        if data_lines:
            chunk = self._parse_chunk("\n".join(data_lines), model_name)
            if chunk is not None:
                yield chunk

    def _parse_chunk(self, data: str, model_name: str) -> ProviderChunk | None:
        if data == "[DONE]":
            return ProviderChunk(done=True, finish_reason="stop")
        try:
            body = json.loads(data)
            self._validate_response_model(body, model_name)
            choice = body.get("choices", [{}])[0]
            delta = choice.get("delta", {})
            text = delta.get("content")
            if text is None:
                text = delta.get("reasoning_content", "")
            finish_reason = choice.get("finish_reason")
            if text is None:
                text = ""
            if not isinstance(text, str):
                raise ValueError
        except (json.JSONDecodeError, IndexError, KeyError, TypeError, ValueError) as exc:
            raise UpstreamResponseError() from exc
        return ProviderChunk(
            text=text,
            finish_reason=finish_reason,
            usage=body.get("usage"),
            done=finish_reason is not None,
        )
