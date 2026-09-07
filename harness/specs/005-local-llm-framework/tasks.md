# Tasks: Framework local de LLMs

**Input**: Design documents from `specs/005-local-llm-framework/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Required by the project constitution and explicitly requested by the feature specification.

## Phase 1: Setup and service separation

- [X] T001 Create `app/services/api`, `app/services/benchmark`, `app/deploy` and `app/services/benchmark/results` directories with ownership comments and runtime ignore rules in `app/.gitignore`.
- [X] T002 [P] Move the current API package, tests, `pyproject.toml`, `Dockerfile` and API README into `app/services/api/` while preserving import behavior during the transition.
- [X] T003 [P] Move `app/benchmark_runner` into `app/services/benchmark/src/benchmark_runner`, move its Dockerfile and create `app/services/benchmark/pyproject.toml` with pinned runtime dependencies.
- [X] T004 Move `app/compose.yaml` to `app/deploy/compose.yaml`, update all build contexts, model mounts, benchmark result mounts and environment paths, and keep service names stable.
- [X] T005 Update `app/.dockerignore`, `app/services/api/.dockerignore`, `app/services/benchmark/.dockerignore` and documentation so models, results, caches and secrets are excluded from images and Git.

## Phase 2: Foundational contracts and package boundary

- [X] T006 [P] Add provider-neutral immutable request, response, chunk, readiness and model-status contracts in `app/services/api/src/local_llm/core/contracts.py` with unit tests in `app/services/api/tests/test_core_contracts.py`.
- [X] T007 Refactor the existing generation service and OVMS adapter to depend on `local_llm.core` contracts, keeping `/v1/generate/*` behavior unchanged in `app/services/api/src/local_llm/application/` and `app/services/api/src/local_llm/infrastructure/`.
- [X] T008 Update API startup, settings and dependency injection to use the new package namespace in `app/services/api/src/local_llm/main.py`, `config.py` and `api/routes.py`.
- [X] T009 [P] Add explicit package metadata, optional extras and the `local-llm` console entry point in `app/services/api/pyproject.toml`; add an import compatibility shim only if existing callers require it.
- [X] T010 [P] Move and update unit/API fixtures and imports under `app/services/api/tests/`, then run the controlled suite before adding new routes.

## Phase 3: User Story 1 - Install and execute a local model (P1) 🎯 MVP

**Independent test**: Install the API package in an isolated environment, inspect a configured alias, start the container stack and receive a local response.

- [X] T011 [P] [US1] Add model manifest and local model inspection types in `app/services/api/src/local_llm/core/model_manifest.py` with tests in `app/services/api/tests/test_model_manifest.py`.
- [X] T012 [US1] Implement `local-llm models list` and `local-llm models info` in `app/services/api/src/local_llm/cli.py`, using configuration without downloading arbitrary paths.
- [X] T013 [US1] Implement `local-llm serve` argument validation and actionable device/model errors in `app/services/api/src/local_llm/cli.py`.
- [X] T014 [US1] Add CLI/package installation tests in `app/services/api/tests/test_cli.py` and update the API Dockerfile to install the package from the moved service root.
- [X] T015 [US1] Update `app/services/api/README.md` and `app/README.md` with installation, model layout, GPU prerequisites and local execution commands.

## Phase 4: User Story 2 - OpenAI-compatible and LangChain use (P2)

**Independent test**: Send one non-streaming and one streaming Chat Completions request and use the endpoint as a `ChatOpenAI` custom base URL.

- [X] T016 [P] [US2] Add typed Chat Completions request, response, choice, usage, message and error schemas in `app/services/api/src/local_llm/api/schemas.py` with validation tests in `app/services/api/tests/test_chat_schemas.py`.
- [X] T017 [P] [US2] Add contract tests for `GET /v1/models` compatibility and `POST /v1/chat/completions` success, validation, unknown model, capacity and upstream failure in `app/services/api/tests/test_chat_api.py`.
- [X] T018 [US2] Implement message-to-text mapping and response mapping in `app/services/api/src/local_llm/application/chat.py` without duplicating provider HTTP logic.
- [X] T019 [US2] Implement `/v1/chat/completions` sync and streaming routes with OpenAI-compatible SSE termination in `app/services/api/src/local_llm/api/routes.py`.
- [X] T020 [US2] Add optional LangChain example and dependency extra under `app/examples/langchain/` and `app/services/api/pyproject.toml`, documenting `ChatOpenAI(base_url=...)` without making LangChain a core dependency.
- [X] T021 [US2] Update OpenAPI assertions and `app/services/api/tests/test_sse.py` for Chat Completions chunks, disconnect cleanup and `[DONE]` behavior.

## Phase 5: User Story 3 - Local model alongside paid providers (P3)

**Independent test**: Use a local alias through the framework and a paid provider through its own client, confirming the local runtime never performs implicit cloud fallback.

- [X] T022 [P] [US3] Add explicit provider-selection and no-implicit-fallback tests in `app/services/api/tests/test_provider_boundary.py`.
- [X] T023 [US3] Document local-vs-remote selection, privacy boundary and credential handling in `app/services/api/README.md` and `app/examples/`.
- [X] T024 [US3] Add configuration validation that rejects unsupported provider forwarding or undeclared remote endpoints in `app/services/api/src/local_llm/config.py`.

## Phase 6: User Story 4 - Isolated benchmark ownership (P3)

**Independent test**: Start the benchmark profile, submit a job through the API, and verify reports appear only under `app/services/benchmark/results/<run-id>`.

- [X] T025 [P] [US4] Add benchmark service tests for job lifecycle, report path safety, model validation and failure status in `app/services/benchmark/tests/test_server.py`.
- [X] T026 [US4] Update benchmark runner imports, working directory, tokenizer mounts and `RESULTS_DIR` handling in `app/services/benchmark/src/benchmark_runner/server.py`.
- [X] T027 [US4] Update API benchmark gateway configuration and route tests so the API submits/queries jobs without importing GuideLLM code in `app/services/api/`.
- [X] T028 [US4] Add benchmark result retention/ignore documentation and migrate existing local result references to `app/services/benchmark/results/` without deleting user reports.
- [X] T029 [US4] Add the benchmark Dockerfile, service manifest and Compose profile validation for `app/services/benchmark/`.

## Phase 7: Performance tuning and verification

- [X] T030 [P] Add configurable `DEFAULT_MAX_TOKENS`, `MAX_TOKENS_LIMIT`, `MAX_CONCURRENCY` and streaming defaults to `app/services/api/.env.example` and documentation, retaining 1.7B as the default model.
- [X] T031 [P] Add model-preparation parameters for an experimental 8B scheduler variant without overwriting the existing model artifacts in `app/scripts/prepare-models.ps1`.
- [X] T032 Add a reproducible benchmark matrix script under `app/services/benchmark/scripts/` for models 1.7B/8B, concurrency 1/2/4 and output 32/128, recording TTFT, latency, tokens/s and errors.
- [X] T033 Validate `docker compose config -q`, API tests, benchmark tests, Ruff and mypy from the new service directories and record results in the feature run report.
- [X] T034 Run Graphify update for `app/` and `harness/`, record graph paths and status under `.agent-work/runs/005-local-llm-framework/`.
- [ ] T035 Review the final diff for secrets, model artifacts, temporary files, unrelated changes and broken relative paths; update quickstart acceptance evidence.

## Dependencies and execution order

- Phase 1 precedes every other phase.
- Phase 2 precedes all user-story phases.
- US1 can complete the MVP after Phase 2.
- US2 depends on the provider-neutral contracts from Phase 2 and the generation service from US1.
- US3 depends on the explicit provider boundary from Phase 2 but does not require remote provider implementation.
- US4 depends on the moved Compose paths from Phase 1 and API gateway settings from Phase 2.
- Performance verification follows US1, US2 and US4 so measurements exercise the final public path.

## Parallel opportunities

- T002/T003 can run in parallel because they own separate service directories.
- T006/T009/T010 can run in parallel after the target layout exists.
- T011 and T016/T017 can be developed in parallel after Phase 2, but route integration waits for the core contracts.
- T025 can run in parallel with API Chat Completions tests because benchmark tests own a separate service.
- T030 and T031 can run in parallel with documentation updates.

## Implementation strategy

1. Complete layout and foundational contracts while preserving the current API.
2. Deliver US1 as the installable local-runtime MVP.
3. Deliver US2 as the interoperability milestone for LangChain and generic clients.
4. Complete benchmark isolation and performance matrix.
5. Run all validation, update Graphify, commit logical groups, then request push confirmation.
