import json

from fastapi.testclient import TestClient

from conftest import FakeProvider
from openvino_models_server.config import Settings
from openvino_models_server.main import create_app


def test_stream_forwards_deltas_and_done() -> None:
    with TestClient(create_app(Settings(), FakeProvider())) as client:
        response = client.post("/v1/generate/stream", json={"text": "Oi"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = response.text.strip().split("\n\n")
    names = [event.splitlines()[0] for event in events]
    payloads = [json.loads(event.split("data: ", 1)[1]) for event in events]
    assert names == ["event: delta", "event: delta", "event: done"]
    assert "resposta" + " stream" == "".join(item["text"] for item in payloads[:2])
    assert payloads[-1]["finish_reason"] == "stop"


def test_stream_encodes_provider_error_as_sse_event() -> None:
    class BrokenProvider(FakeProvider):
        async def stream(self, parameters, request_id):  # type: ignore[no-untyped-def]
            del parameters, request_id
            from openvino_models_server.infrastructure.errors import UpstreamResponseError

            raise UpstreamResponseError()
            yield  # pragma: no cover

    with TestClient(create_app(Settings(), BrokenProvider())) as client:
        response = client.post("/v1/generate/stream", json={"text": "Oi"})

    assert "event: error" in response.text
    assert '"code":"upstream_failed"' in response.text
