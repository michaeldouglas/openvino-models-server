---

description: "Tasks for the framework package and runtime structure refactor"
---

# Tasks: Estrutura de pacotes e runtime

**Input**: `spec.md` and `plan.md` in this feature directory.

## Phase 1: Structure and ownership

- [X] T001 [US1] Create the feature branch and record the branch decision in the run evidence.
- [X] T002 [US1] Move the installable API from `app/services/api` to `app/packages/local-llm`.
- [X] T003 [US1] Move the benchmark from `app/services/benchmark` to `app/packages/benchmark-runner`, preserving existing results.
- [X] T004 [US1] Group deployment, model assets and preparation scripts under `app/runtime`.
- [X] T005 [US1] Remove the obsolete empty `local_llm.infrastructure` package after its modules are moved to adapters.

## Phase 2: Explicit package layers

- [X] T006 [US3] Move HTTP modules to `local_llm.interfaces.http` and provider/benchmark clients to `local_llm.adapters`.
- [X] T007 [US3] Update imports and tests while keeping the public `local_llm` namespace and `local-llm` entry point unchanged.
- [X] T008 [US3] Verify `local_llm.core` remains independent of FastAPI, HTTPX, OVMS and LangChain.

## Phase 3: Runtime integration and documentation

- [X] T009 [US2] Update Compose, Docker contexts, model mounts, result mounts and environment paths for the new tree.
- [X] T010 [US2] Update ignore rules so model weights, caches, benchmark results and local secrets remain untracked.
- [X] T011 [US1] Update app, package, harness and feature documentation with the new ownership boundaries and commands.

## Phase 4: Validation and handoff

- [X] T012 [US2] Run API and benchmark pytest suites from their new package locations.
- [X] T013 [US2] Run Ruff, mypy, editable installation/CLI checks and PowerShell syntax validation.
- [X] T014 [US2] Validate Docker Compose configuration without starting services.
- [X] T015 [US1] Update Graphify for the app and harness, review the diff for generated artifacts/secrets, and record evidence under `.agent-work`.
- [X] T016 [US1] Create the local feature commit after all validations pass.

## Dependencies

- T002–T005 establish the target tree before T006–T011 can be completed.
- T006–T011 must be complete before T012–T014 provide meaningful validation.
- T015 and T016 are final handoff tasks and must run after all file changes.

## Acceptance checklist

- `app` no longer exposes `services`, `deploy`, `models` or `scripts` as active product roots.
- Existing local model files and benchmark results are present in their new locations and are not staged.
- API, benchmark, CLI, Compose and package contracts remain valid.
- The commit contains only source, configuration, documentation and feature artifacts required for the refactor.
