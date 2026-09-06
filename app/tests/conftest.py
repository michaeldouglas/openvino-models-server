from collections.abc import AsyncIterator

import pytest

from openvino_models_server.application.generation import (
    GenerationParameters,
    ModelStatus,
    ProviderChunk,
    ProviderResult,
    Readiness,
)


class FakeProvider:
    default_model = "test-model"
    model_names = ("test-model", "other-model")

    def __init__(self, ready: bool = True) -> None:
        self.ready = ready
        self.sync_calls = 0
        self.async_calls = 0
        self.prompts: list[str] = []

    def generate_sync(self, parameters: GenerationParameters, request_id: str) -> ProviderResult:
        del request_id
        self.sync_calls += 1
        self.prompts.append(parameters.text)
        return ProviderResult(
            parameters.model_name or self.default_model,
            "resposta sync",
            "stop",
            {"total_tokens": 2},
        )

    async def generate_async(
        self, parameters: GenerationParameters, request_id: str
    ) -> ProviderResult:
        del request_id
        self.async_calls += 1
        self.prompts.append(parameters.text)
        return ProviderResult(parameters.model_name or self.default_model, "resposta async", "stop")

    async def stream(
        self, parameters: GenerationParameters, request_id: str
    ) -> AsyncIterator[ProviderChunk]:
        del parameters, request_id
        yield ProviderChunk(text="resposta")
        yield ProviderChunk(text=" stream", finish_reason="stop", done=True)

    async def readiness(self) -> Readiness:
        return Readiness(self.ready, None if self.ready else "model_unavailable")

    async def model_statuses(self) -> tuple[ModelStatus, ...]:
        return tuple(
            ModelStatus(name, self.ready, None if self.ready else "model_unavailable")
            for name in self.model_names
        )


@pytest.fixture
def fake_provider() -> FakeProvider:
    return FakeProvider()
