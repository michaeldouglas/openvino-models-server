from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

RESULTS_DIR = Path(os.getenv("RESULTS_DIR", "/results")).resolve()
OVMS_URL = os.getenv("OVMS_URL", "http://ovms:8000").rstrip("/")
MAX_ACTIVE_JOBS = int(os.getenv("BENCHMARK_MAX_ACTIVE", "1"))
RUN_ID_PATTERN = re.compile(r"^benchmark-[0-9]{8}-[0-9]{6}-[a-f0-9]{8}$")
MODEL_PATHS = {
    "qwen3-1.7b": "/models/qwen3-1.7b",
    "qwen3-8b": "/models/qwen3-8b",
}
REPORTS: dict[str, tuple[str, str]] = {
    "html": ("benchmarks.html", "text/html"),
    "json": ("benchmarks.json", "application/json"),
    "csv": ("benchmarks.csv", "text/csv"),
}


class BenchmarkInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(min_length=1, max_length=128)
    prompt_tokens: int = Field(ge=1, le=4096)
    output_tokens: int = Field(ge=1, le=512)
    concurrency: int = Field(ge=1, le=32)
    max_requests: int = Field(ge=1, le=1000)
    max_duration_seconds: int = Field(ge=0, le=3600)


class JobResponse(BaseModel):
    run_id: str
    model: str
    status: Literal["running", "completed", "failed"]
    results_path: str
    files: list[str] = Field(default_factory=list)
    successful_requests: int | None = None
    errored_requests: int | None = None
    error: str | None = None


@dataclass
class Job:
    run_id: str
    request: BenchmarkInput
    status: Literal["running", "completed", "failed"] = "running"
    files: list[str] = field(default_factory=list)
    successful_requests: int | None = None
    errored_requests: int | None = None
    error: str | None = None


jobs: dict[str, Job] = {}
jobs_lock = asyncio.Lock()
active_jobs = 0

app = FastAPI(title="GuideLLM benchmark runner", version="0.1.0")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "alive"}


@app.post("/internal/v1/benchmarks", response_model=JobResponse, status_code=202)
async def create_benchmark(request: BenchmarkInput) -> JobResponse:
    global active_jobs
    if request.model not in MODEL_PATHS:
        raise HTTPException(status_code=422, detail="Modelo não permitido.")
    if not Path(MODEL_PATHS[request.model]).is_dir():
        raise HTTPException(status_code=503, detail="Tokenizer do modelo não está disponível.")

    async with jobs_lock:
        if active_jobs >= MAX_ACTIVE_JOBS:
            raise HTTPException(status_code=409, detail="Capacidade de benchmark ocupada.")
        active_jobs += 1
        run_id = _new_run_id()
        job = Job(run_id=run_id, request=request)
        jobs[run_id] = job

    asyncio.create_task(_execute(job))
    return _job_response(job)


@app.get("/internal/v1/benchmarks/{run_id}", response_model=JobResponse)
async def benchmark_status(run_id: str) -> JobResponse:
    return _job_response(_get_job(run_id))


@app.get("/internal/v1/benchmarks/{run_id}/report")
async def benchmark_report(
    run_id: str,
    format: Literal["html", "json", "csv"] = Query(default="html"),
) -> FileResponse:
    job = _get_job(run_id)
    if job.status != "completed":
        raise HTTPException(status_code=409, detail="Relatório ainda não está pronto.")
    filename, media_type = REPORTS[format]
    run_root = (RESULTS_DIR / run_id).resolve()
    report_path = (run_root / filename).resolve()
    if not _is_child(report_path, run_root) or not report_path.is_file():
        raise HTTPException(status_code=404, detail="Relatório não encontrado.")
    return FileResponse(report_path, media_type=media_type, filename=filename)


def _new_run_id() -> str:
    now = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"benchmark-{now}-{uuid.uuid4().hex[:8]}"


def _get_job(run_id: str) -> Job:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise HTTPException(status_code=404, detail="Execução não encontrada.")
    job = jobs.get(run_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Execução não encontrada.")
    return job


def _job_response(job: Job) -> JobResponse:
    return JobResponse(
        run_id=job.run_id,
        model=job.request.model,
        status=job.status,
        results_path=f"/results/{job.run_id}",
        files=job.files,
        successful_requests=job.successful_requests,
        errored_requests=job.errored_requests,
        error=job.error,
    )


async def _execute(job: Job) -> None:
    global active_jobs
    run_root = RESULTS_DIR / job.run_id
    log_path = run_root / "run.log"
    try:
        run_root.mkdir(parents=True, exist_ok=False)
        _write_manifest(job, run_root / "run-manifest.json")
        preflight_code = (
            "import urllib.request; "
            f"r=urllib.request.urlopen('{OVMS_URL}/v1/models', timeout=5); "
            "print(r.status); raise SystemExit(0 if r.status == 200 else 1)"
        )
        preflight_code_value = await _run_process(
            [sys.executable, "-c", preflight_code], log_path
        )
        if preflight_code_value != 0:
            raise RuntimeError("OVMS preflight failed")
        return_code = await _run_process(_guidellm_command(job), log_path)
        _finish_from_reports(job, run_root, return_code)
    except Exception:
        job.status = "failed"
        job.error = "O executor não conseguiu concluir o benchmark."
        if run_root.is_dir():
            _write_manifest(job, run_root / "run-manifest.json")
    finally:
        async with jobs_lock:
            active_jobs -= 1


async def _run_process(command: list[str], log_path: Path) -> int:
    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=str(RESULTS_DIR),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    output, _ = await process.communicate()
    with log_path.open("ab") as log:
        log.write(output or b"")
    return process.returncode or 0


def _guidellm_command(job: Job) -> list[str]:
    request = job.request
    backend = {
        "kind": "openai_http",
        "target": OVMS_URL,
        "model": request.model,
        "request_format": "/v1/chat/completions",
        "stream": True,
        "validate_backend": False,
        "extras": {
            "body": {
                "temperature": 0.2,
                "stream_options": {"continuous_usage_stats": None},
            }
        },
    }
    profile = "kind=synchronous"
    if request.concurrency > 1:
        profile = f"kind=concurrent,streams={request.concurrency}"
    run_root = f"/results/{job.run_id}"
    return [
        "guidellm",
        "run",
        "--backend",
        json.dumps(backend, separators=(",", ":")),
        "--profile",
        profile,
        "--data",
        f"kind=synthetic_text,prompt_tokens={request.prompt_tokens},output_tokens={request.output_tokens}",
        "--tokenizer",
        f"kind=huggingface_auto,model={MODEL_PATHS[request.model]}",
        "--constraint",
        f"kind=max_requests,count={request.max_requests}",
        "--metrics",
        f"kind=generative,sample_size={request.max_requests},prefer_response_metrics=false",
        "--output",
        f"kind=json,path={run_root}/benchmarks.json",
        "--output",
        f"kind=csv,path={run_root}/benchmarks.csv",
        "--output",
        f"kind=html,path={run_root}/benchmarks.html",
    ] + (
        ["--constraint", f"kind=max_duration,seconds={request.max_duration_seconds}"]
        if request.max_duration_seconds > 0
        else []
    )


def _finish_from_reports(job: Job, run_root: Path, return_code: int) -> None:
    expected = [filename for filename, _ in REPORTS.values()]
    if return_code != 0 or any(not (run_root / filename).is_file() for filename in expected):
        raise RuntimeError("GuideLLM report generation failed")
    report = json.loads((run_root / "benchmarks.json").read_text(encoding="utf-8"))
    benchmark = report["benchmarks"][0]
    state = benchmark["scheduler_state"]
    job.successful_requests = int(state["successful_requests"])
    job.errored_requests = int(state["errored_requests"])
    if job.successful_requests < 1 or job.errored_requests > 0:
        raise RuntimeError("GuideLLM completed without a valid successful sample")
    job.files = expected
    job.status = "completed"
    _write_manifest(job, run_root / "run-manifest.json")


def _write_manifest(job: Job, path: Path) -> None:
    if not path.parent.is_dir():
        return
    payload = {
        "run_id": job.run_id,
        "model": job.request.model,
        "status": job.status,
        "results_path": f"/results/{job.run_id}",
        "files": job.files,
        "successful_requests": job.successful_requests,
        "errored_requests": job.errored_requests,
        "error": job.error,
        "ovms_url": OVMS_URL,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _is_child(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
