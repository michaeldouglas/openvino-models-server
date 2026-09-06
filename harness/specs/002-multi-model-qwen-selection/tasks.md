# Tasks: Seleção entre modelos Qwen

**Input**: Design documents from `harness/specs/002-multi-model-qwen-selection/`

**Tests**: Included because the feature changes public API behavior and model routing.

## Phase 1: Setup

- [x] T001 [P] [US3] Document the two model definitions, default alias and persistent model directory in `app/.env.example` and `app/README.md`.
- [x] T002 [P] [US3] Add the idempotent model preparation script at `app/scripts/prepare-models.ps1`.
- [x] T003 [P] [US2] Add the multi-model OVMS configuration contract and Compose startup arguments in `app/compose.yaml`.

## Phase 2: Foundational

- [x] T004 [US1] Add a validated model catalog and default alias to `app/src/openvino_models_server/config.py`.
- [x] T005 [US1] Extend the application inference protocol with model resolution and model status types in `app/src/openvino_models_server/application/generation.py`.
- [x] T006 [US1] Add model selection validation and safe unknown-model errors in `app/src/openvino_models_server/infrastructure/errors.py` and `application/generation.py`.
- [x] T007 [US2] Add catalog and model-status response schemas in `app/src/openvino_models_server/api/schemas.py`.

## Phase 3: User Story 1 - Escolher o modelo por requisição (Priority: P1)

- [x] T008 [P] [US1] Add request-schema coverage for the optional model field in `app/tests/test_api.py`.
- [x] T009 [P] [US1] Add OVMS payload coverage proving the selected model is forwarded in `app/tests/test_ovms_client.py`.
- [x] T010 [US1] Update `app/src/openvino_models_server/infrastructure/ovms_client.py` to send the resolved model and preserve response identity.
- [x] T011 [US1] Update `app/src/openvino_models_server/api/routes.py` so sync, async and stream use the request-specific model.
- [x] T012 [US1] Add tests for default selection, explicit selection, unknown selection and isolation in `app/tests/test_api.py`.

## Phase 4: User Story 2 - Consultar modelos disponíveis (Priority: P2)

- [x] T013 [P] [US2] Add controlled upstream model-status parsing and unavailable-state tests in `app/tests/test_ovms_client.py`.
- [x] T014 [US2] Implement `GET /v1/models` and default-model readiness behavior in `app/src/openvino_models_server/api/routes.py`.
- [x] T015 [US2] Add OpenAPI and response assertions for `/v1/models` in `app/tests/test_api.py`.

## Phase 5: User Story 3 - Preparar os dois artefatos (Priority: P3)

- [x] T016 [US3] Add the allowlisted, resumable preparation command and validation of required model files in `app/scripts/prepare-models.ps1`.
- [x] T017 [US3] Add generated-configuration and Compose syntax validation instructions in `harness/specs/002-multi-model-qwen-selection/quickstart.md`.
- [ ] T018 [US3] Prepare and run a real Qwen3-8B GPU smoke test, recording evidence in `harness/.agent-work`; do not mark complete from mocks.

## Phase 6: Polish and quality

- [x] T019 [P] Update `app/README.md` with model aliases, examples, limitations and rollback guidance.
- [x] T020 [P] Update the OpenAPI contract at `harness/specs/002-multi-model-qwen-selection/contracts/openapi.yaml`.
- [x] T021 Run tests, Ruff and mypy through the harness runner and record outputs in `harness/.agent-work`.
- [x] T022 Review Graphify output after code changes and update the app graph.

## Dependencies and execution order

- T001-T003 establish configuration and preparation conventions.
- T004-T007 block route work.
- T008-T012 implement and verify request-level selection.
- T013-T015 implement and verify the catalog.
- T016-T017 implement offline preparation documentation.
- T018 depends on the prepared Qwen3-8B artifact and real Docker/Intel GPU access.
- T019-T022 are final validation and evidence tasks.

## Implementation strategy

Keep the 1.7B as the default. Add the 8B to the allowlist and persistent repository without downloading it during this code change. The real 8B preparation and GPU acceptance remain explicitly gated by available disk, memory, and user confirmation.
