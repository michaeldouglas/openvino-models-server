# Implementation Plan: Estrutura de pacotes e runtime

**Branch**: `feature/reorganize-framework-structure` | **Date**: 2026-09-07

## Summary

Reorganizar o monorepo local para que o pacote instalável, o benchmark e os
artefatos de execução tenham ownership explícito. A mudança será mecânica e
behavior-preserving: mover `services/api` para `packages/local-llm`, mover o
benchmark para `packages/benchmark-runner`, e agrupar deployment, modelos e
scripts em `runtime/`.

## Technical Context

**Language/Version**: Python 3.13, PowerShell, Docker Compose

**Primary Dependencies**: FastAPI, HTTPX, Pydantic Settings, Uvicorn, OVMS,
GuideLLM

**Storage**: `app/runtime/models` para pesos/cache e
`app/packages/benchmark-runner/results` para resultados locais

**Testing**: pytest, Ruff, mypy, Compose config validation

**Target Platform**: Windows/WSL2 com Docker Desktop e Linux Intel compatível

**Project Type**: Python packages + CLI + HTTP service + benchmark service

**Constraints**: preservar `local_llm`, `local-llm`, APIs HTTP e configuração
local; não versionar modelos, resultados, caches ou segredos

## Design Decisions

1. `packages/local-llm` representa o produto distribuível e contém `core`,
   `application`, `adapters` e `interfaces`.
2. `packages/benchmark-runner` é um pacote separado porque possui ciclo de
   vida, dependências e outputs próprios.
3. `runtime/` agrupa deployment, modelos e scripts, pois todos pertencem à
   preparação/execução local e não ao pacote Python.
4. O namespace público `local_llm` não muda; somente o caminho do projeto muda.
5. Não será introduzido um padrão pesado. A refatoração usa Move Method/Move
   Class conceptualmente apenas onde necessário e mantém módulos simples.

## Target Structure

```text
app/
├── packages/
│   ├── local-llm/
│   │   ├── src/local_llm/
│   │   │   ├── core/
│   │   │   ├── application/
│   │   │   ├── adapters/ovms/
│   │   │   └── interfaces/http/
│   │   └── tests/
│   └── benchmark-runner/
│       ├── src/benchmark_runner/
│       ├── tests/
│       ├── scripts/
│       └── results/
├── runtime/
│   ├── deployment/
│   ├── models/
│   └── scripts/
├── examples/
└── README.md
```

## Migration and Validation

1. Move directories without deleting model artifacts or benchmark reports.
2. Update relative paths in Compose, Dockerfiles, README, scripts and
   quickstart/spec artifacts.
3. Keep `.env` at `app/.env` for this feature and point deployment to it;
   migrate only the example file into `runtime/deployment`.
4. Verify no tracked reference points to the old `services`, `deploy`,
   `app/models` or `app/scripts` paths as active paths.
5. Run API/benchmark tests, Ruff, mypy, editable installation and Compose
   config validation.
6. Update app/harness Graphify and record the evidence in `.agent-work`.
