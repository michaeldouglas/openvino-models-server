# Quickstart: Framework local de LLMs

## Prerequisites

- Python 3.13 for the package/CLI path.
- Docker Desktop with WSL2 and an Intel GPU for the OVMS server path.
- A prepared Qwen3 model in `app/models`.

## Install and inspect

From `app/services/api` in the final layout:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
local-llm models list
```

Expected result: the aliases and their readiness/device metadata are displayed
without downloading model weights into the package directory.

## Start the local server

From `app/deploy`:

```powershell
docker compose up -d --build
Invoke-RestMethod http://127.0.0.1:8000/readyz
```

Expected result: readiness reports `ready` after OVMS and the selected model
are healthy.

## OpenAI-compatible request

```powershell
$body = @{
  model = "qwen3-1.7b"
  messages = @(@{ role = "user"; content = "Explique OpenVINO em uma frase." })
  max_tokens = 32
  stream = $false
} | ConvertTo-Json -Depth 6
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/v1/chat/completions -ContentType application/json -Body $body
```

## LangChain compatibility

Install the optional extra and point `ChatOpenAI` at
`http://127.0.0.1:8000/v1` with a local placeholder API key. Verify both
`invoke` and `stream` against the same model alias.

## Benchmark

Run the benchmark profile and verify that reports are created below
`app/services/benchmark/results/<run-id>/`, not in the API source tree. Record
model, device, token targets, concurrency, success/error counts, TTFT, latency
and tokens/s for each comparison.

## Validation checklist

1. `pytest` passes for API, provider and benchmark tests.
2. Ruff and mypy pass for each service package.
3. `docker compose config -q` passes from `app/deploy`.
4. Health/readiness and both chat response modes work.
5. A short benchmark has at least one successful request and no errors.

## Evidence from this feature

- The API service suite passes 31 tests, including legacy generation, model
  manifests, CLI, OpenAI-compatible chat, streaming and provider boundaries.
- The benchmark service suite passes 4 tests, including report safety and
  GuideLLM command construction.
- Ruff and mypy pass independently for both service packages.
- `docker compose --profile benchmark-api --profile benchmark -f
  app/deploy/compose.yaml config -q` passes.
- Graphify was updated at `app/graphify-out/graph.json` and
  `harness/graphify-out/graph.json`.
- A real GPU/model benchmark remains an environment acceptance step because it
  requires starting Docker/OVMS and is not part of the deterministic test
  suite.
