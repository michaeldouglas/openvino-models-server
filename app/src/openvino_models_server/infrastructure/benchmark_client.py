from __future__ import annotations

from typing import Any

import httpx

from openvino_models_server.application.benchmarking import (
    BenchmarkGateway,
    BenchmarkJob,
    BenchmarkSpec,
)
from openvino_models_server.config import Settings
from openvino_models_server.infrastructure.errors import (
    BenchmarkCapacityError,
    BenchmarkFailedError,
    BenchmarkNotFoundError,
    BenchmarkNotReadyError,
    BenchmarkUnavailableError,
)


class BenchmarkClient(BenchmarkGateway):
    """Async HTTP gateway to the isolated GuideLLM executor."""

    def __init__(self, settings: Settings) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.benchmark_runner_url.rstrip("/"),
            timeout=httpx.Timeout(settings.benchmark_timeout_seconds),
        )

    async def submit(self, spec: BenchmarkSpec, request_id: str) -> BenchmarkJob:
        try:
            response = await self._client.post(
                "/internal/v1/benchmarks",
                json={
                    "model": spec.model,
                    "prompt_tokens": spec.prompt_tokens,
                    "output_tokens": spec.output_tokens,
                    "concurrency": spec.concurrency,
                    "max_requests": spec.max_requests,
                    "max_duration_seconds": spec.max_duration_seconds,
                },
                headers={"X-Request-ID": request_id},
            )
        except httpx.HTTPError as exc:
            raise BenchmarkUnavailableError() from exc
        return self._parse_job(response)

    async def status(self, run_id: str, request_id: str) -> BenchmarkJob:
        try:
            response = await self._client.get(
                f"/internal/v1/benchmarks/{run_id}",
                headers={"X-Request-ID": request_id},
            )
        except httpx.HTTPError as exc:
            raise BenchmarkUnavailableError() from exc
        return self._parse_job(response)

    async def report(
        self, run_id: str, report_format: str, request_id: str
    ) -> tuple[bytes, str]:
        try:
            response = await self._client.get(
                f"/internal/v1/benchmarks/{run_id}/report",
                params={"format": report_format},
                headers={"X-Request-ID": request_id},
            )
        except httpx.HTTPError as exc:
            raise BenchmarkUnavailableError() from exc
        if response.status_code == 404:
            raise BenchmarkNotFoundError()
        if response.status_code == 409:
            raise BenchmarkNotReadyError()
        if response.status_code >= 400:
            raise BenchmarkFailedError()
        return response.content, response.headers.get("content-type", "application/octet-stream")

    async def aclose(self) -> None:
        await self._client.aclose()

    def _parse_job(self, response: httpx.Response) -> BenchmarkJob:
        if response.status_code == 404:
            raise BenchmarkNotFoundError()
        if response.status_code == 409:
            raise BenchmarkCapacityError()
        if response.status_code >= 500:
            raise BenchmarkUnavailableError()
        if response.status_code >= 400:
            raise BenchmarkFailedError()
        try:
            body: Any = response.json()
            return BenchmarkJob(
                run_id=str(body["run_id"]),
                model=str(body["model"]),
                status=str(body["status"]),
                results_path=str(body["results_path"]),
                files=tuple(str(item) for item in body.get("files", [])),
                successful_requests=self._optional_int(body.get("successful_requests")),
                errored_requests=self._optional_int(body.get("errored_requests")),
                error=str(body["error"]) if body.get("error") else None,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise BenchmarkFailedError() from exc

    @staticmethod
    def _optional_int(value: object) -> int | None:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            return int(value)
        raise ValueError("expected integer value")
