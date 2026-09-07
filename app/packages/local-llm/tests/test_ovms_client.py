import asyncio
import json

import httpx

from local_llm.adapters.errors import UpstreamResponseError
from local_llm.adapters.ovms.client import OVMSClient
from local_llm.application.generation import GenerationParameters
from local_llm.config import Settings


def test_sync_client_maps_openai_compatible_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        payload = json.loads(request.content)
        assert payload["chat_template_kwargs"] == {"enable_thinking": False}
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
    result = client.generate_sync(GenerationParameters("Oi", 8, 0.2, "qwen3-8b"), "request-1")
    client.close()
    assert result.text == "ok"


def test_sync_client_forwards_selected_model_alias() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["model"] == "qwen3-8b"
        return httpx.Response(
            200,
            json={
                "model": "qwen3-8b",
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
            },
            request=request,
        )

    client = OVMSClient(Settings())
    client._sync_client.close()
    client._sync_client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://test"
    )
    result = client.generate_sync(GenerationParameters("Oi", 8, 0.2, "qwen3-8b"), "request-1")
    client.close()
    assert result.model == "qwen3-8b"


def test_sync_client_rejects_response_for_another_model() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "model": "qwen3-1.7b",
                "choices": [{"message": {"content": "unexpected"}, "finish_reason": "stop"}],
            },
            request=request,
        )

    client = OVMSClient(Settings())
    client._sync_client.close()
    client._sync_client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://test"
    )
    try:
        client.generate_sync(GenerationParameters("Oi", 8, 0.2, "qwen3-8b"), "request-1")
    except UpstreamResponseError:
        pass
    else:
        raise AssertionError("expected a model mismatch to be rejected")
    finally:
        client.close()


def test_async_client_uses_stream_true_and_parses_sse() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        payload = json.loads(request.content)
        assert payload["stream"] is True
        assert payload["chat_template_kwargs"] == {"enable_thinking": False}
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


def test_model_statuses_map_servables_to_aliases() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/models"
        return httpx.Response(
            200,
            json={"data": [{"id": "qwen3-1.7b"}]},
            request=request,
        )

    async def run() -> tuple[object, ...]:
        client = OVMSClient(Settings())
        await client._async_client.aclose()
        client._async_client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler), base_url="http://test"
        )
        statuses = await client.model_statuses()
        await client.aclose()
        return statuses

    statuses = asyncio.run(run())
    assert statuses[0].model_name == "qwen3-1.7b"
    assert statuses[0].ready is True
    assert statuses[1].ready is False
