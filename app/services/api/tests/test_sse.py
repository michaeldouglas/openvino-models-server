import json

from fastapi.testclient import TestClient

from conftest import FakeProvider
from local_llm.config import Settings
from local_llm.main import create_app


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
            from local_llm.infrastructure.errors import UpstreamResponseError

            raise UpstreamResponseError()
            yield  # pragma: no cover

    with TestClient(create_app(Settings(), BrokenProvider())) as client:
        response = client.post("/v1/generate/stream", json={"text": "Oi"})

    assert "event: error" in response.text
    assert '"code":"upstream_failed"' in response.text


def test_chat_stream_uses_openai_data_chunks_and_done_marker() -> None:
    with TestClient(create_app(Settings(), FakeProvider())) as client:
        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Oi"}],
                "stream": True,
            },
        )

    assert response.status_code == 200
    events = [
        line.removeprefix("data: ")
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    assert json.loads(events[0])["choices"][0]["delta"]["role"] == "assistant"
    assert json.loads(events[1])["choices"][0]["delta"]["content"] == "resposta"
    assert json.loads(events[2])["choices"][0]["delta"]["content"] == " stream"
    assert json.loads(events[3])["choices"][0]["finish_reason"] == "stop"
    assert events[4] == "[DONE]"
