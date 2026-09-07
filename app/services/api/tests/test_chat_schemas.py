import pytest
from pydantic import ValidationError

from local_llm.api.schemas import ChatCompletionRequest


def test_chat_request_accepts_only_declared_message_fields() -> None:
    request = ChatCompletionRequest(
        messages=[{"role": "user", "content": "Oi"}],
        stream=True,
    )

    assert request.messages[0].role == "user"
    assert request.stream is True


def test_chat_request_rejects_blank_message_and_extra_provider_fields() -> None:
    with pytest.raises(ValidationError):
        ChatCompletionRequest(messages=[{"role": "user", "content": " "}])
    with pytest.raises(ValidationError):
        ChatCompletionRequest(
            messages=[{"role": "user", "content": "Oi"}],
            provider="openai",
        )
