# Contract: benchmark routes

Base URL: API FastAPI local (`http://127.0.0.1:8000`).

## POST `/v1/benchmarks`

Creates a benchmark without waiting for completion. Response status is `202`.

Request:

```json
{
  "model": "qwen3-8b",
  "prompt_tokens": 32,
  "output_tokens": 32,
  "concurrency": 1,
  "max_requests": 1,
  "max_duration_seconds": 0
}
```

All fields except `model` have conservative defaults. `model` defaults to the
configured benchmark model. The API rejects unknown fields, invalid ranges and
models not allowed by the executor configuration.

Response `202`:

```json
{
  "run_id": "benchmark-20260907-120000-a1b2c3d4",
  "model": "qwen3-8b",
  "status": "running",
  "results_path": "/results/benchmark-20260907-120000-a1b2c3d4",
  "files": []
}
```

## GET `/v1/benchmarks/{run_id}`

Returns status, counts and generated file names. Unknown IDs return `404`.
Executor failure returns status `failed` and a safe public error.

## GET `/v1/benchmarks/{run_id}/report?format=json|csv|html`

Returns the selected report only after completion. The default format is
`html`. The API never accepts a filesystem path. An unknown format returns
`422`; a report that is not ready returns `409`.

## Error envelope

Errors follow the existing API shape:

```json
{
  "error": {
    "code": "benchmark_unavailable",
    "message": "O executor de benchmark está indisponível.",
    "request_id": "..."
  }
}
```

Possible codes include `invalid_request`, `benchmark_unavailable`,
`benchmark_capacity`, `benchmark_not_found`, `benchmark_not_ready` and
`benchmark_failed`.
