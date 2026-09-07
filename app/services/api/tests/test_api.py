from fastapi.testclient import TestClient

from conftest import FakeBenchmarkGateway, FakeProvider
from local_llm.api.schemas import HealthResponse
from local_llm.config import Settings
from local_llm.main import create_app


def make_client(
    provider: FakeProvider | None = None,
    benchmark_gateway: FakeBenchmarkGateway | None = None,
) -> TestClient:
    settings = Settings(max_input_chars=20, default_max_tokens=16, max_tokens_limit=64)
    return TestClient(
        create_app(
            settings,
            provider or FakeProvider(),
            benchmark_gateway or FakeBenchmarkGateway(),
        )
    )


def test_sync_and_async_return_common_contract() -> None:
    provider = FakeProvider()
    with make_client(provider) as client:
        sync = client.post("/v1/generate/sync", json={"text": "Oi", "max_tokens": 8})
        asynchronous = client.post("/v1/generate/async", json={"text": "Oi"})

    assert sync.status_code == 200
    assert sync.json()["text"] == "resposta sync"
    assert set(("request_id", "model", "text", "finish_reason")).issubset(sync.json())
    assert asynchronous.status_code == 200
    assert asynchronous.json()["text"] == "resposta async"
    assert provider.sync_calls == 1
    assert provider.async_calls == 1


def test_explicit_model_is_accepted_and_default_is_preserved() -> None:
    provider = FakeProvider()
    with make_client(provider) as client:
        selected = client.post(
            "/v1/generate/sync", json={"model": "other-model", "text": "Oi"}
        )
        default = client.post("/v1/generate/sync", json={"text": "Oi"})

    assert selected.status_code == 200
    assert default.status_code == 200
    assert selected.json()["model"] == "other-model"
    assert default.json()["model"] == "test-model"
    assert provider.prompts == ["Oi", "Oi"]


def test_unknown_model_is_rejected_before_provider() -> None:
    provider = FakeProvider()
    with make_client(provider) as client:
        response = client.post(
            "/v1/generate/sync", json={"model": "not-allowed", "text": "Oi"}
        )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "model_not_found"
    assert provider.sync_calls == 0


def test_blank_input_is_rejected_before_provider() -> None:
    provider = FakeProvider()
    with make_client(provider) as client:
        response = client.post("/v1/generate/sync", json={"text": "   "})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
    assert provider.sync_calls == 0


def test_configured_input_limit_is_enforced() -> None:
    provider = FakeProvider()
    with make_client(provider) as client:
        response = client.post("/v1/generate/async", json={"text": "123456789012345678901"})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_request"
    assert provider.async_calls == 0


def test_readiness_does_not_generate() -> None:
    with make_client(FakeProvider(ready=False)) as client:
        response = client.get("/readyz")
        health = client.get("/healthz")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "reason": "model_unavailable"}
    assert health.status_code == 200
    assert HealthResponse.model_validate(health.json()).status == "alive"


def test_openapi_has_exact_generation_routes() -> None:
    with make_client() as client:
        paths = client.get("/openapi.json").json()["paths"]

    assert set(paths) >= {
        "/v1/generate/sync",
        "/v1/generate/async",
        "/v1/generate/stream",
        "/healthz",
        "/readyz",
        "/v1/models",
    }


def test_models_catalog_marks_default_and_status() -> None:
    with make_client() as client:
        response = client.get("/v1/models")

    assert response.status_code == 200
    assert response.json()["object"] == "list"
    assert response.json()["data"][0]["default"] is True


def test_chat_completion_maps_messages_to_local_generation_contract() -> None:
    provider = FakeProvider()
    with make_client(provider) as client:
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "other-model",
                "messages": [{"role": "user", "content": "Oi"}],
                "max_tokens": 8,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["object"] == "chat.completion"
    assert body["model"] == "other-model"
    assert body["choices"][0]["message"] == {
        "role": "assistant",
        "content": "resposta async",
    }
    assert provider.prompts == ["user: Oi"]


def test_chat_completion_rejects_unconfigured_model_without_provider_call() -> None:
    provider = FakeProvider()
    with make_client(provider) as client:
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "remote-provider",
                "messages": [{"role": "user", "content": "Oi"}],
            },
        )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "model_not_found"
    assert provider.async_calls == 0


def test_benchmark_submission_returns_job_without_waiting() -> None:
    gateway = FakeBenchmarkGateway()
    with make_client(benchmark_gateway=gateway) as client:
        response = client.post(
            "/v1/benchmarks",
            json={"model": "other-model", "prompt_tokens": 16, "output_tokens": 8},
        )

    assert response.status_code == 202
    assert response.json()["status"] == "running"
    assert gateway.submitted[0].model == "other-model"
    assert gateway.submitted[0].max_requests == 1


def test_benchmark_status_and_report_are_scoped_to_run() -> None:
    with make_client() as client:
        status = client.get("/v1/benchmarks/benchmark-20260907-120000-a1b2c3d4")
        report = client.get(
            "/v1/benchmarks/benchmark-20260907-120000-a1b2c3d4/report?format=html"
        )

    assert status.status_code == 200
    assert status.json()["successful_requests"] == 1
    assert report.status_code == 200
    assert report.headers["content-type"] == "text/html; charset=utf-8"


def test_benchmark_rejects_unknown_fields_and_invalid_report_format() -> None:
    with make_client() as client:
        unknown_field = client.post("/v1/benchmarks", json={"command": "rm -rf"})
        invalid_format = client.get(
            "/v1/benchmarks/benchmark-20260907-120000-a1b2c3d4/report?format=xml"
        )

    assert unknown_field.status_code == 422
    assert invalid_format.status_code == 422
