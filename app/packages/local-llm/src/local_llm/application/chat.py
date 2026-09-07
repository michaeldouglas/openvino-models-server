from __future__ import annotations

from local_llm.interfaces.http.schemas import (
    ChatChoiceMessage,
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    GenerationRequest,
)


def to_generation_request(request: ChatCompletionRequest) -> GenerationRequest:
    text = "\n".join(f"{message.role}: {message.content}" for message in request.messages)
    return GenerationRequest(
        model=request.model,
        text=text,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
    )


def to_chat_response(
    request_id: str,
    model: str,
    text: str,
    finish_reason: str,
    usage: dict[str, object] | None,
    created: int,
) -> ChatCompletionResponse:
    return ChatCompletionResponse(
        id=f"chatcmpl-{request_id}",
        created=created,
        model=model,
        choices=[
            ChatCompletionChoice(
                message=ChatChoiceMessage(content=text), finish_reason=finish_reason
            )
        ],
        usage=usage,
    )
