import asyncio

import httpx

from openvino_models_server.application.generation import GenerationParameters
from openvino_models_server.config import Settings
from openvino_models_server.infrastructure.ovms_client import OVMSClient


def test_sync_client_maps_openai_compatible_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        assert request.read()[0:0] == b""
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]},
            request=request,
        )

    client = OVMSClient(Settings())
    client._sync_client.close()
    client._sync_client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://test"
    )
    result = client.generate_sync(GenerationParameters("Oi", 8, 0.2), "request-1")
    client.close()
    assert result.text == "ok"


def test_async_client_uses_stream_true_and_parses_sse() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=(
                b'data: {"choices":[{"delta":{"content":"A"},"finish_reason":null}]}\n\n'
                b'data: {"choices":[{"delta":{"content":"B"},"finish_reason":"stop"}]}\n\n'
            ),
            request=request,
        )

    async def run() -> list[str]:
        client = OVMSClient(Settings())
        await client._async_client.aclose()
        client._async_client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler), base_url="http://test"
        )
        chunks = [
            chunk async for chunk in client.stream(GenerationParameters("Oi", 8, 0.2), "request-1")
        ]
        await client.aclose()
        return [chunk.text for chunk in chunks]

    assert asyncio.run(run()) == ["A", "B"]
