from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from openvino_models_server.api.routes import router
from openvino_models_server.api.schemas import ErrorDetails, ErrorResponse
from openvino_models_server.application.benchmarking import BenchmarkGateway
from openvino_models_server.application.generation import GenerationService, InferenceProvider
from openvino_models_server.config import Settings, get_settings
from openvino_models_server.infrastructure.benchmark_client import BenchmarkClient
from openvino_models_server.infrastructure.errors import InferenceError
from openvino_models_server.infrastructure.ovms_client import OVMSClient


def create_app(
    settings: Settings | None = None,
    provider: InferenceProvider | None = None,
    benchmark_gateway: BenchmarkGateway | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    resolved_provider = provider or OVMSClient(resolved_settings)
    resolved_benchmark_gateway = benchmark_gateway or BenchmarkClient(resolved_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.generation_service = GenerationService(resolved_settings, resolved_provider)
        app.state.benchmark_gateway = resolved_benchmark_gateway
        yield
        close = getattr(resolved_provider, "aclose", None)
        if close is not None:
            await close()
        await resolved_benchmark_gateway.aclose()

    app = FastAPI(
        title="OpenVINO Model Server API",
        version="0.1.0",
        description="Geração de texto em três modalidades por OVMS na GPU Intel.",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        request.state.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    app.add_exception_handler(RequestValidationError, _validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(InferenceError, _inference_error_handler)  # type: ignore[arg-type]
    app.include_router(router)
    return app


async def _validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    error = ErrorResponse(
        error=ErrorDetails(
            code="invalid_request",
            message="O corpo ou os parâmetros da solicitação são inválidos.",
            request_id=request.state.request_id,
        )
    )
    return JSONResponse(status_code=422, content=error.model_dump())


async def _inference_error_handler(request: Request, exc: InferenceError) -> JSONResponse:
    error = ErrorResponse(
        error=ErrorDetails(
            code=exc.code,
            message=exc.public_message,
            request_id=request.state.request_id,
        )
    )
    return JSONResponse(status_code=exc.status_code, content=error.model_dump())


app = create_app()
