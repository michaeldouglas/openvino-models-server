from fastapi.testclient import TestClient

from conftest import FakeProvider
from local_llm.config import Settings
from local_llm.main import create_app


def test_chat_route_is_documented_and_uses_declared_model_catalog() -> None:
    with TestClient(create_app(Settings(), FakeProvider())) as client:
        openapi = client.get("/openapi.json").json()
        models = client.get("/v1/models")

    assert "/v1/chat/completions" in openapi["paths"]
    assert models.json()["data"][0]["id"] == "test-model"


def test_chat_route_returns_structured_upstream_error() -> None:
    class BrokenProvider(FakeProvider):
        async def generate_async(self, parameters, request_id):  # type: ignore[no-untyped-def]
            del parameters, request_id
            from local_llm.adapters.errors import UpstreamResponseError

            raise UpstreamResponseError()

    with TestClient(create_app(Settings(), BrokenProvider())) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "Oi"}]},
        )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "upstream_failed"
