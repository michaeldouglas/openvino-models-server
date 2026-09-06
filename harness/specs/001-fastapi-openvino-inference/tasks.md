# Tasks: OpenVINO Model Server API

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/openapi.yaml`
**Target**: `C:/Users/mdbaa/development/Agents/server-agents/app`

## Phase 1: Foundation

- [X] T001 [P] [US1] Configure `app/pyproject.toml` with pinned runtime and test dependencies, scripts and src layout.
- [X] T002 [P] [US3] Create `app/src/openvino_models_server/config.py` with validated environment settings and safe defaults.
- [X] T003 [P] [US1] Create typed request, result, error and stream schemas in `app/src/openvino_models_server/api/schemas.py`.
- [X] T004 [P] [US1] Define the small inference provider protocol and domain error types in `app/src/openvino_models_server/application/generation.py` and `app/src/openvino_models_server/infrastructure/errors.py`.
- [X] T005 [P] [US1] Add controlled provider fixtures and request validation tests under `app/tests/`.

## Phase 2: User Story 1 - Complete generation

- [X] T006 [US1] Implement OVMS sync and async HTTP clients with connection reuse, timeout and response mapping in `app/src/openvino_models_server/infrastructure/ovms_client.py`.
- [X] T007 [US1] Implement generation service with shared validation, bounded concurrency and safe error translation in `app/src/openvino_models_server/application/generation.py`.
- [X] T008 [US1] Implement `/v1/generate/sync` and `/v1/generate/async` in `app/src/openvino_models_server/api/routes.py` without blocking async I/O.
- [X] T009 [US1] Add sync/async success, validation, upstream failure, timeout and isolation tests in `app/tests/test_api.py` and `app/tests/test_ovms_client.py`.

## Phase 3: User Story 2 - Incremental generation

- [X] T010 [US2] Implement bounded OVMS SSE parsing and cleanup on timeout/disconnect in `app/src/openvino_models_server/infrastructure/ovms_client.py`.
- [X] T011 [US2] Implement `/v1/generate/stream` with `delta`, `done` and `error` events in `app/src/openvino_models_server/api/routes.py`.
- [X] T012 [US2] Add fragmented SSE, empty delta, done, upstream error and disconnect tests in `app/tests/test_sse.py`.

## Phase 4: User Story 3 - Operable Compose stack

- [X] T013 [P] [US3] Create `app/src/openvino_models_server/main.py` with FastAPI lifecycle, health and readiness endpoints.
- [X] T014 [P] [US3] Create `app/Dockerfile`, `app/compose.yaml`, `app/.env.example`, `app/.dockerignore` updates and `app/models/.gitkeep` with explicit GPU configuration and persistent model volume.
- [X] T015 [P] [US3] Document architecture, model candidates, preparation gate, Windows/Linux commands, Swagger and curl examples in `app/README.md`.
- [X] T016 [US3] Add health/readiness, OpenAPI and configuration tests in `app/tests/test_api.py`.

## Phase 5: Quality and evidence

- [X] T017 [P] [US1] Run Ruff, type checking and the complete controlled test suite through `harness/scripts/Invoke-AgentCommand.ps1`, routing outputs to the exclusive run directory.
- [X] T018 [P] [US3] Validate Compose syntax and Dockerfile/configuration without starting the model service when GPU/model prerequisites are absent.
- [X] T019 [US1] Run `graphify update C:/Users/mdbaa/development/Agents/server-agents/app` and record the app graph location.
- [ ] T020 [US3] Record runtime/image/model/GPU evidence and real-generation/benchmark results, or the exact blocked prerequisites, in `harness/.agent-work/runs/<run-id>/openvino-engineer/reports/`.
- [X] T021 [US1] Perform independent findings-first review with `quality-reviewer`; assign any correction tasks before code edits.

## Dependencies and execution order

T001-T005 are foundational. T006-T009 depend on T001-T005. T010-T012 depend
on the provider boundary from T006-T008. T013-T016 may proceed after the
foundation and share route/lifecycle ownership serially. T017-T021 run after
implementation and are required before the local commit. The real runtime gate
is not replaced by mocks.
