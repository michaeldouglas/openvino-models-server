from fastapi.testclient import TestClient

from conftest import FakeProvider
from openvino_models_server.api.schemas import HealthResponse
from openvino_models_server.config import Settings
from openvino_models_server.main import create_app


def make_client(provider: FakeProvider | None = None) -> TestClient:
    settings = Settings(max_input_chars=20, default_max_tokens=16, max_tokens_limit=64)
    return TestClient(create_app(settings, provider or FakeProvider()))


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
    }
