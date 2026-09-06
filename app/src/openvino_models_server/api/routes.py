from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse

from openvino_models_server.api.schemas import (
    ErrorDetails,
    GenerationRequest,
    GenerationResponse,
    HealthResponse,
    ReadinessResponse,
)
from openvino_models_server.application.generation import GenerationService
from openvino_models_server.infrastructure.errors import InferenceError

router = APIRouter()


def get_service(request: Request) -> GenerationService:
    return cast(GenerationService, request.app.state.generation_service)


def _sse(event: str, data: dict[str, object]) -> str:
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {encoded}\n\n"


@router.get("/healthz", response_model=HealthResponse, tags=["operational"])
async def healthz() -> HealthResponse:
    return HealthResponse(status="alive")


@router.get("/readyz", response_model=ReadinessResponse, tags=["operational"])
async def readyz(
    service: Annotated[GenerationService, Depends(get_service)]
) -> ReadinessResponse | JSONResponse:
    readiness = await service.readiness()
    if readiness.ready:
        return ReadinessResponse(status="ready")
    body = ReadinessResponse(status="not_ready", reason=readiness.reason)
    return JSONResponse(status_code=503, content=body.model_dump())


@router.post("/v1/generate/sync", response_model=GenerationResponse, tags=["generation"])
def generate_sync(
    request_body: GenerationRequest,
    request: Request,
    service: Annotated[GenerationService, Depends(get_service)],
) -> GenerationResponse:
    return service.generate_sync(request_body, request.state.request_id)


@router.post("/v1/generate/async", response_model=GenerationResponse, tags=["generation"])
async def generate_async(
    request_body: GenerationRequest,
    request: Request,
    service: Annotated[GenerationService, Depends(get_service)],
) -> GenerationResponse:
    return await service.generate_async(request_body, request.state.request_id)


@router.post("/v1/generate/stream", tags=["generation"])
async def generate_stream(
    request_body: GenerationRequest,
    request: Request,
    service: Annotated[GenerationService, Depends(get_service)],
) -> StreamingResponse:
    request_id = request.state.request_id

    async def events() -> AsyncIterator[str]:
        emitted_done = False
        try:
            async for chunk in service.stream(request_body, request_id):
                if chunk.text or not chunk.done:
                    yield _sse(
                        "delta",
                        {
                            "request_id": request_id,
                            "model": service.provider.model_name,
                            "text": chunk.text,
                        },
                    )
                if chunk.done:
                    emitted_done = True
                    yield _sse(
                        "done",
                        {
                            "request_id": request_id,
                            "model": service.provider.model_name,
                            "finish_reason": chunk.finish_reason or "stop",
                            "usage": chunk.usage,
                        },
                    )
            if not emitted_done:
                yield _sse(
                    "done",
                    {
                        "request_id": request_id,
                        "model": service.provider.model_name,
                        "finish_reason": "stop",
                    },
                )
        except InferenceError as exc:
            yield _sse(
                "error",
                {
                    "error": ErrorDetails(
                        code=exc.code, message=exc.public_message, request_id=request_id
                    ).model_dump()
                },
            )

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
