from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from openvino_models_server.application.generation import (
    GenerationParameters,
    ProviderChunk,
    ProviderResult,
    Readiness,
)
from openvino_models_server.config import Settings
from openvino_models_server.infrastructure.errors import (
    GenerationTimeoutError,
    UpstreamResponseError,
    UpstreamUnavailableError,
)


class OVMSClient:
    """OpenAI-compatible OVMS adapter with one reusable client per protocol."""

    def __init__(self, settings: Settings) -> None:
        self.model_name = settings.ovms_model_name
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
        return self._parse_result(response)

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
        return self._parse_result(response)

    async def stream(
        self, parameters: GenerationParameters, request_id: str
    ) -> AsyncIterator[ProviderChunk]:
        try:
            async with self._async_client.stream(
                "POST", "/v1/chat/completions", json=self._payload(parameters, request_id, True)
            ) as response:
                if response.status_code >= 400:
                    raise UpstreamResponseError()
                async for chunk in self._iter_sse(response):
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
        try:
            response = await self._async_client.get("/v1/models")
        except httpx.HTTPError:
            return Readiness(False, "upstream_unavailable")
        if response.status_code >= 400:
            return Readiness(False, "model_unavailable")
        try:
            body = response.json()
        except ValueError:
            return Readiness(False, "upstream_failed")
        models = body.get("data", []) if isinstance(body, dict) else []
        ids = {item.get("id") for item in models if isinstance(item, dict)}
        if ids and self.model_name not in ids:
            return Readiness(False, "model_unavailable")
        return Readiness(True)

    async def aclose(self) -> None:
        await self._async_client.aclose()
        self._sync_client.close()

    def close(self) -> None:
        self._sync_client.close()

    def _payload(
        self, parameters: GenerationParameters, request_id: str, stream: bool
    ) -> dict[str, Any]:
        return {
            "model": self.model_name,
            "messages": [{"role": "user", "content": parameters.text}],
            "max_tokens": parameters.max_tokens,
            "temperature": parameters.temperature,
            "chat_template_kwargs": {"enable_thinking": False},
            "stream": stream,
            "user": request_id,
        }

    def _parse_result(self, response: httpx.Response) -> ProviderResult:
        if response.status_code >= 400:
            raise UpstreamResponseError()
        try:
            body = response.json()
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
            self.model_name,
            text,
            finish_reason,
            usage if isinstance(usage, dict) else None,
        )

    async def _iter_sse(self, response: httpx.Response) -> AsyncIterator[ProviderChunk]:
        data_lines: list[str] = []
        current_size = 0
        async for line in response.aiter_lines():
            current_size += len(line.encode("utf-8"))
            if current_size > self._max_event_bytes:
                raise UpstreamResponseError()
            if not line:
                if data_lines:
                    chunk = self._parse_chunk("\n".join(data_lines))
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
            chunk = self._parse_chunk("\n".join(data_lines))
            if chunk is not None:
                yield chunk

    def _parse_chunk(self, data: str) -> ProviderChunk | None:
        if data == "[DONE]":
            return ProviderChunk(done=True, finish_reason="stop")
        try:
            body = json.loads(data)
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
