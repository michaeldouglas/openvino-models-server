# Tasks: Fast Local LLM Performance Profile

**Input**: Design documents from `/specs/007-performance-fast-profile/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Required because this feature changes runtime behavior and adds operational telemetry.

## Phase 1: Setup

- [X] T001 Add the fast deployment profile files under `app/runtime/deployment/profiles/fast/` and preserve the existing full profile
- [X] T002 [P] Document fast and quality startup commands and tuning variables in `app/README.md` and `app/packages/local-llm/README.md`
- [X] T003 [P] Add the performance profile configuration fields and safe defaults to `app/packages/local-llm/src/local_llm/config.py` and `app/runtime/deployment/.env.example`

## Phase 2: Foundational

- [X] T004 Add typed generation measurement helpers in `app/packages/local-llm/src/local_llm/core/performance.py` without storing prompt or response content
- [X] T005 [P] Add unit tests for measurement serialization and token-rate derivation in `app/packages/local-llm/tests/test_performance.py`
- [X] T006 [P] Add configuration tests for profile names and concurrency bounds in `app/packages/local-llm/tests/test_config.py`

## Phase 3: User Story 1 - Usar o perfil rápido (Priority: P1)

**Goal**: Start a deployment that loads only the latency-oriented 1.7B model and exposes it as the only enabled API model.

**Independent Test**: Compose config validates, the fast OVMS config references only the 1.7B model, and API settings expose the matching model catalog.

- [X] T007 [US1] Add the fast OVMS model configuration at `app/runtime/deployment/profiles/fast/config.json`
- [X] T008 [US1] Add `app/runtime/deployment/compose.fast.yaml` with the fast model mount, API model catalog override, configurable fast concurrency, and existing GPU/cache settings
- [X] T009 [US1] Add a Compose/config regression test or validation script under `app/runtime/deployment/` that verifies the fast profile contains only `qwen3-1.7b`
- [X] T010 [US1] Update `app/runtime/scripts/prepare-models.ps1` and deployment documentation so the fast profile fails clearly when the 1.7B artifact is missing

**Checkpoint**: The fast profile is independently startable and does not load the optional 8B model.

## Phase 4: User Story 2 - Ajustar capacidade com segurança (Priority: P2)

**Goal**: Make runtime capacity explicit and validated while preserving existing error behavior and generation routes.

**Independent Test**: The API accepts valid concurrency configuration, rejects invalid configuration at startup, and all existing generation tests remain green.

- [X] T011 [P] [US2] Extend `app/packages/local-llm/src/local_llm/config.py` with a named performance profile and validated capacity settings
- [X] T012 [P] [US2] Add configuration and capacity tests in `app/packages/local-llm/tests/test_config.py` and `app/packages/local-llm/tests/test_api.py`
- [X] T013 [US2] Ensure `app/runtime/deployment/compose.fast.yaml` maps API concurrency to the OVMS sequence profile without silently changing the full deployment
- [X] T014 [US2] Update `app/runtime/deployment/.env.example` with the fast-profile override and explain latency versus throughput trade-offs

**Checkpoint**: Users can tune capacity through environment/configuration without code changes or contract changes.

## Phase 5: User Story 3 - Medir e comparar performance (Priority: P3)

**Goal**: Emit safe generation timing telemetry and preserve benchmark evidence for controlled comparisons.

**Independent Test**: Sync, async, and streaming requests emit timing events with no prompt leakage; benchmark configuration remains reproducible.

- [X] T015 [US3] Instrument sync, async, and streaming generation in `app/packages/local-llm/src/local_llm/application/generation.py` using the typed measurement helper
- [X] T016 [P] [US3] Add service tests in `app/packages/local-llm/tests/test_performance.py` for total latency, TTFT, usage-derived output tokens, and failure outcomes
- [X] T017 [US3] Add a benchmark matrix guide and report fields in `app/packages/benchmark-runner/README.md` and `app/packages/benchmark-runner/scripts/run-matrix.ps1` without changing existing benchmark endpoints
- [X] T018 [US3] Add a controlled local benchmark script under `app/packages/benchmark-runner/scripts/` that records warmup, model, device, concurrency, TTFT, total latency, tokens per second, and Docker resource snapshots

**Checkpoint**: Two benchmark runs can be compared without changing public generation response schemas.

## Phase 6: Polish and validation

- [X] T019 [P] Run package tests, typing, lint, and OpenAPI route validation for `app/packages/local-llm/`
- [X] T020 [P] Run benchmark-runner tests and Compose config validation for the full and fast profiles
- [X] T021 Run the quickstart smoke test with the fast profile when containers are explicitly authorized and available
- [X] T022 Update the feature quickstart and implementation evidence under `harness/.agent-work/runs/`

## Dependencies & Execution Order

- Phase 1 precedes all implementation.
- Phase 2 is foundational and must complete before user stories.
- US1 can be implemented independently after Phase 2.
- US2 depends on the profile names established by US1 but does not depend on telemetry.
- US3 depends on the capacity settings from US2 for meaningful benchmark labels.
- Phase 6 follows all user stories.

## Parallel Opportunities

- T002 and T003 can run in parallel.
- T005 and T006 can run in parallel after T004's contract is defined.
- T011 and T012 can be prepared in parallel, then T013/T014 follow.
- T016 and T017 can run in parallel after T015's measurement contract is agreed.
- T019 and T020 can run in parallel.

## Implementation Strategy

1. Deliver the fast profile first and validate its Compose/config contract.
2. Add safe configurable capacity while preserving the existing full deployment.
3. Add timing telemetry and a reproducible benchmark matrix.
4. Run tests and only then perform the container smoke test and hardware benchmark.
