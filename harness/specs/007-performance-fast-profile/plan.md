# Implementation Plan: Fast Local LLM Performance Profile

**Branch**: `feature/performance-fast-profile` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-performance-fast-profile/spec.md`

**Note**: This template is filled in by the `$speckit-plan` command; its definition describes the execution workflow.

## Summary

Provide a fast local profile that loads only the latency-oriented Qwen3 1.7B by
default, makes the API/OVMS capacity relationship explicit, and adds safe
generation timing telemetry plus reproducible benchmark documentation. Keep the
existing OpenAI-compatible and legacy generation contracts unchanged. Runtime
tuning remains configurable and evidence-driven rather than hard-coded to a
single hardware claim.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.13; YAML/PowerShell for deployment and model profiles

**Primary Dependencies**: FastAPI, Pydantic Settings, httpx, Uvicorn, OpenVINO Model Server 2026.3.1 GPU image, Docker Compose

**Storage**: Mounted model repository and compiled-model cache; benchmark reports remain under the benchmark package results directory

**Testing**: pytest, OpenAPI smoke checks, Docker Compose config validation, controlled API benchmark with warmup and fixed iterations

**Target Platform**: Docker Desktop/WSL2 on Windows with Intel GPU passthrough; Linux Docker remains compatible

**Project Type**: FastAPI service plus Dockerized local inference runtime and benchmark runner

**Performance Goals**: Warm requests must expose TTFT, total latency, output tokens, and tokens/second; the fast profile must be comparable across concurrency 1, 2, and 4 without changing public response contracts

**Constraints**: Do not load the optional 8B model in the fast profile; preserve max-token and input validation; do not log complete prompts or responses; do not claim an optimal setting without a measured comparison

**Scale/Scope**: One local host, one OVMS process, one default fast deployment entrypoint, optional 1.7B and 8B assets, up to 32 validated API concurrency slots

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

PASS: The plan uses the installed skills, preserves typed FastAPI contracts, keeps runtime configuration external, adds tests for changed behavior, and includes Docker smoke validation. No secrets or model artifacts are added to source control. Performance values will be measured on the real device rather than presented as universal defaults.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file ($speckit-plan command output)
├── research.md          # Phase 0 output ($speckit-plan command)
├── data-model.md        # Phase 1 output ($speckit-plan command)
├── quickstart.md        # Phase 1 output ($speckit-plan command)
├── contracts/           # Phase 1 output ($speckit-plan command)
└── tasks.md             # Phase 2 output ($speckit-tasks command - NOT created by $speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
app/
├── packages/local-llm/
│   ├── src/local_llm/
│   └── tests/
├── packages/benchmark-runner/
│   └── tests/
└── runtime/
    ├── deployment/
    │   ├── compose.yaml
    │   ├── .env.example
    │   └── profiles/
    ├── models/
    └── scripts/

harness/specs/007-performance-fast-profile/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

**Structure Decision**: Keep API code, benchmark code, and inference deployment
separate under `app/packages` and `app/runtime`. The deployment directory has one
Compose entrypoint whose default configuration is the fast 1.7B profile; profile
metadata remains under `runtime/deployment/profiles`, while model artifacts stay
mounted and ignored. Timing concerns stay at the service boundary and are
represented by typed internal measurement data, not by coupling the API to OVMS
internals.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | The feature stays within the existing API, runtime, and benchmark packages. |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
