import logging
import time

from fastapi.testclient import TestClient

from conftest import FakeBenchmarkGateway, FakeProvider
from local_llm.config import Settings
from local_llm.core.performance import GenerationMeasurement
from local_llm.main import create_app


def test_measurement_derives_output_rate_after_first_token() -> None:
    measurement = GenerationMeasurement("qwen3-1.7b", True, 2)
    measurement.started_at = time.perf_counter() - 1.0
    measurement.observe_first_token()
    measurement.ttft_ms = 100.0
    measurement.started_at = time.perf_counter() - 1.1

    measurement.finish(usage={"completion_tokens": 10}, outcome="success")

    fields = measurement.as_dict()
    assert fields["model"] == "qwen3-1.7b"
    assert fields["ttft_ms"] == 100.0
    assert fields["output_tokens"] == 10
    assert fields["output_tokens_per_second"] is not None
    assert fields["outcome"] == "success"


def test_measurement_does_not_contain_prompt_or_response() -> None:
    measurement = GenerationMeasurement("qwen3-1.7b", False, 2)

    fields = measurement.as_dict()

    assert "text" not in fields
    assert "prompt" not in fields
    assert "response" not in fields


def test_generation_logs_safe_timing_event(caplog) -> None:
    caplog.set_level(logging.INFO, logger="uvicorn.error")
    prompt = "segredo que não deve aparecer"
    settings = Settings(max_input_chars=100, default_max_tokens=16, max_tokens_limit=64)

    with TestClient(create_app(settings, FakeProvider(), FakeBenchmarkGateway())) as client:
        response = client.post("/v1/generate/sync", json={"text": prompt, "max_tokens": 8})

    assert response.status_code == 200
    assert "generation_performance" in caplog.text
    assert prompt not in caplog.text
