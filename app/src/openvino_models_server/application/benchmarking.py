from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class BenchmarkSpec:
    model: str
    prompt_tokens: int
    output_tokens: int
    concurrency: int
    max_requests: int
    max_duration_seconds: int


@dataclass(frozen=True)
class BenchmarkJob:
    run_id: str
    model: str
    status: str
    results_path: str
    files: tuple[str, ...]
    successful_requests: int | None = None
    errored_requests: int | None = None
    error: str | None = None


class BenchmarkGateway(Protocol):
    async def submit(self, spec: BenchmarkSpec, request_id: str) -> BenchmarkJob: ...

    async def status(self, run_id: str, request_id: str) -> BenchmarkJob: ...

    async def report(
        self, run_id: str, report_format: str, request_id: str
    ) -> tuple[bytes, str]: ...

    async def aclose(self) -> None: ...
