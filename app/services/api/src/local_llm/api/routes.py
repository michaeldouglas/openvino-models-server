from __future__ import annotations

import json
import time
import uuid
from collections.abc import AsyncIterator
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from local_llm.api.schemas import (
    BenchmarkRequest,
    BenchmarkResponse,
    ChatChunkDelta,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ErrorDetails,
    GenerationRequest,
    GenerationResponse,
    HealthResponse,
    ModelListResponse,
    ModelStatusResponse,
    ReadinessResponse,
)
from local_llm.application.benchmarking import (
    BenchmarkGateway,
    BenchmarkJob,
    BenchmarkSpec,
)
from local_llm.application.chat import to_chat_response, to_generation_request
from local_llm.application.generation import GenerationService
from local_llm.infrastructure.errors import InferenceError, ModelNotFoundError

router = APIRouter()


def get_service(request: Request) -> GenerationService:
    return cast(GenerationService, request.app.state.generation_service)


def get_benchmark_gateway(request: Request) -> BenchmarkGateway:
    return cast(BenchmarkGateway, request.app.state.benchmark_gateway)


def _benchmark_response(job: BenchmarkJob) -> BenchmarkResponse:
    return BenchmarkResponse(
        run_id=job.run_id,
        model=job.model,
        status=job.status,  # type: ignore[arg-type]
        results_path=job.results_path,
        files=list(job.files),
        successful_requests=job.successful_requests,
        errored_requests=job.errored_requests,
        error=job.error,
    )


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


@router.get("/v1/models", response_model=ModelListResponse, tags=["operational"])
async def models(
    service: Annotated[GenerationService, Depends(get_service)],
) -> ModelListResponse:
    statuses = await service.model_statuses()
    return ModelListResponse(
        data=[
            ModelStatusResponse(
                id=status.model_name,
                model=status.model_name,
                status="ready" if status.ready else "unavailable",
                default=status.model_name == service.provider.default_model,
                reason=status.reason,
            )
            for status in statuses
        ]
    )


def _openai_sse(payload: object) -> str:
    encoded = (
        "[DONE]"
        if payload == "[DONE]"
        else json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )
    return f"data: {encoded}\n\n"


@router.post(
    "/v1/benchmarks",
    response_model=BenchmarkResponse,
    status_code=202,
    tags=["benchmarks"],
    summary="Iniciar benchmark do OVMS",
)
async def create_benchmark(
    request_body: BenchmarkRequest,
    request: Request,
    service: Annotated[GenerationService, Depends(get_service)],
    gateway: Annotated[BenchmarkGateway, Depends(get_benchmark_gateway)],
) -> BenchmarkResponse:
    model = request_body.model or service.settings.benchmark_default_model
    if model not in service.provider.model_names:
        raise ModelNotFoundError()
    spec = BenchmarkSpec(
        model=model,
        prompt_tokens=request_body.prompt_tokens,
        output_tokens=request_body.output_tokens,
        concurrency=request_body.concurrency,
        max_requests=request_body.max_requests,
        max_duration_seconds=request_body.max_duration_seconds,
    )
    job = await gateway.submit(spec, request.state.request_id)
    return _benchmark_response(job)


@router.get(
    "/v1/benchmarks/{run_id}",
    response_model=BenchmarkResponse,
    tags=["benchmarks"],
)
async def benchmark_status(
    run_id: str,
    request: Request,
    gateway: Annotated[BenchmarkGateway, Depends(get_benchmark_gateway)],
) -> BenchmarkResponse:
    job = await gateway.status(run_id, request.state.request_id)
    return _benchmark_response(job)


@router.get("/v1/benchmarks/{run_id}/report", tags=["benchmarks"])
async def benchmark_report(
    run_id: str,
    request: Request,
    gateway: Annotated[BenchmarkGateway, Depends(get_benchmark_gateway)],
    format: Literal["html", "json", "csv"] = "html",
) -> Response:
    content, media_type = await gateway.report(run_id, format, request.state.request_id)
    return Response(content=content, media_type=media_type.split(";", 1)[0])


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
    model_name = service.resolve_model(request_body)

    async def events() -> AsyncIterator[str]:
        emitted_done = False
        try:
            async for chunk in service.stream(request_body, request_id):
                if chunk.text or not chunk.done:
                    yield _sse(
                        "delta",
                        {
                            "request_id": request_id,
                            "model": model_name,
                            "text": chunk.text,
                        },
                    )
                if chunk.done:
                    emitted_done = True
                    yield _sse(
                        "done",
                        {
                            "request_id": request_id,
                            "model": model_name,
                            "finish_reason": chunk.finish_reason or "stop",
                            "usage": chunk.usage,
                        },
                    )
            if not emitted_done:
                yield _sse(
                    "done",
                    {
                        "request_id": request_id,
                        "model": model_name,
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


@router.post("/v1/chat/completions", response_model=None, tags=["chat"])
async def chat_completions(
    request_body: ChatCompletionRequest,
    request: Request,
    service: Annotated[GenerationService, Depends(get_service)],
) -> ChatCompletionResponse | StreamingResponse:
    request_id = request.state.request_id
    generation_request = to_generation_request(request_body)
    model_name = service.resolve_model(generation_request)
    created = int(time.time())
    completion_id = f"chatcmpl-{uuid.uuid4().hex}"

    if not request_body.stream:
        result = await service.generate_async(generation_request, request_id)
        return to_chat_response(
            request_id,
            result.model,
            result.text,
            result.finish_reason,
            result.usage,
            created,
        )

    async def events() -> AsyncIterator[str]:
        try:
            yield _openai_sse(
                ChatCompletionChunk(
                    id=completion_id,
                    created=created,
                    model=model_name,
                    choices=[
                        ChatCompletionChunkChoice(
                            delta=ChatChunkDelta(role="assistant")
                        )
                    ],
                ).model_dump(exclude_none=True)
            )
            async for chunk in service.stream(generation_request, request_id):
                if chunk.text:
                    yield _openai_sse(
                        ChatCompletionChunk(
                            id=completion_id,
                            created=created,
                            model=model_name,
                            choices=[
                                ChatCompletionChunkChoice(
                                    delta=ChatChunkDelta(content=chunk.text)
                                )
                            ],
                        ).model_dump(exclude_none=True)
                    )
                if chunk.done:
                    yield _openai_sse(
                        ChatCompletionChunk(
                            id=completion_id,
                            created=created,
                            model=model_name,
                            choices=[
                                ChatCompletionChunkChoice(
                                    delta=ChatChunkDelta(),
                                    finish_reason=chunk.finish_reason or "stop",
                                )
                            ],
                            usage=chunk.usage,
                        ).model_dump(exclude_none=True)
                    )
                    break
            yield _openai_sse("[DONE]")
        except InferenceError as exc:
            yield _openai_sse(
                {
                    "error": ErrorDetails(
                        code=exc.code,
                        message=exc.public_message,
                        request_id=request_id,
                    ).model_dump()
                }
            )

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
