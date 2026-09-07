from dataclasses import FrozenInstanceError

import pytest

from local_llm.core.contracts import GenerationParameters, ProviderChunk


def test_generation_contracts_are_immutable() -> None:
    parameters = GenerationParameters("Oi", 32, 0.2, "qwen3-1.7b")

    with pytest.raises(FrozenInstanceError):
        parameters.text = "alterado"  # type: ignore[misc]


def test_provider_chunk_defaults_to_non_terminal_delta() -> None:
    chunk = ProviderChunk(text="Oi")

    assert chunk.done is False
    assert chunk.finish_reason is None
