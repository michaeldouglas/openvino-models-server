from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


def _usage_count(usage: Mapping[str, Any] | None) -> int | None:
    if usage is None:
        return None
    for key in ("completion_tokens", "output_tokens"):
        value = usage.get(key)
        if isinstance(value, int) and value >= 0:
            return value
    return None


@dataclass
class GenerationMeasurement:
    """Safe timing data for one generation without prompt/response content."""

    model: str
    streaming: bool
    max_concurrency: int
    profile: str = "default"
    request_id: str = ""
    started_at: float = field(default_factory=time.perf_counter)
    ttft_ms: float | None = None
    total_latency_ms: float | None = None
    output_tokens: int | None = None
    output_tokens_per_second: float | None = None
    outcome: str = "running"

    def observe_first_token(self) -> None:
        if self.ttft_ms is None:
            self.ttft_ms = self._elapsed_ms()

    def finish(self, *, usage: Mapping[str, Any] | None, outcome: str) -> None:
        self.total_latency_ms = self._elapsed_ms()
        self.output_tokens = _usage_count(usage)
        generation_ms = self.total_latency_ms
        if self.ttft_ms is not None:
            generation_ms -= self.ttft_ms
        if self.output_tokens is not None and self.output_tokens > 0 and generation_ms > 0:
            self.output_tokens_per_second = self.output_tokens / (generation_ms / 1000)
        self.outcome = outcome

    def as_dict(self) -> dict[str, object]:
        return {
            "model": self.model,
            "request_id": self.request_id,
            "streaming": self.streaming,
            "max_concurrency": self.max_concurrency,
            "profile": self.profile,
            "ttft_ms": _rounded(self.ttft_ms),
            "total_latency_ms": _rounded(self.total_latency_ms),
            "output_tokens": self.output_tokens,
            "output_tokens_per_second": _rounded(self.output_tokens_per_second),
            "outcome": self.outcome,
        }

    def _elapsed_ms(self) -> float:
        return (time.perf_counter() - self.started_at) * 1000


def _rounded(value: float | None) -> float | None:
    return None if value is None else round(value, 3)
