# Implementation Plan: Framework local de LLMs

**Branch**: `feature/performance-and-layout` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

## Summary

Transformar a aplicação atual em um produto Python instalável, mantendo o
runtime OpenVINO/OVMS como backend local e oferecendo uma superfície
OpenAI-compatible para clientes comuns e LangChain. A mudança será incremental:
primeiro separar fisicamente API, benchmark, deploy e resultados; depois extrair
contratos públicos estáveis, adicionar Chat Completions com streaming e fornecer
uma CLI mínima para inspeção/execução local. O benchmark consumirá o endpoint
público e manterá seus relatórios dentro de `packages/benchmark-runner/results`.

## Technical Context

**Language/Version**: Python 3.13, PowerShell para preparação local e Docker Compose para o runtime de servidor.

**Primary Dependencies**: FastAPI, Pydantic Settings, HTTPX, Uvicorn, OpenVINO Model Server 2026.3.1 GPU, GuideLLM 0.7.3; LangChain será integração opcional e não dependência do núcleo.

**Storage**: Artefatos de modelos em `app/runtime/models` (fora do pacote); relatórios descartáveis em `app/packages/benchmark-runner/results`; configuração por `.env` e manifestos versionáveis.

**Testing**: pytest, pytest-cov, Ruff, mypy, validação de OpenAPI, `docker compose config`, smoke HTTP e benchmark curto condicionado à disponibilidade de GPU/modelo.

**Target Platform**: Windows 11/WSL2 com Docker Desktop e GPU Intel Arc, além de Linux com dispositivo Intel compatível documentado.

**Project Type**: Python package + CLI + HTTP service + optional benchmark service.

**Performance Goals**: Preservar ou melhorar o baseline medido: 1.7B com TTFT mediano próximo de 136 ms e 8B próximo de 347 ms para a carga de 32/32; medir 8B com `max_num_seqs` 1 e 2 sob concorrência 1/2/4 sem aumentar erros.

**Constraints**: Sem pesos no pacote ou Git; fallback remoto opt-in; API existente deve continuar funcionando; streaming deve liberar o primeiro delta sem esperar a resposta completa; benchmark não pode compartilhar código de execução com a API.

**Scale/Scope**: Um host local, dois modelos Qwen3 atuais, um processo API e um serviço de benchmark isolado; preparado para novos providers sem implementar todos eles nesta feature.

## Constitution Check

*GATE: PASS — reavaliado após o design abaixo.*

- Skills-first: este plano usa Spec Kit, Python design patterns, refactoring guidance, Docker, OpenVINO benchmark e type/testing guidance.
- FastAPI contracts: `/v1/chat/completions`, `/v1/models`, health/readiness e rotas legadas terão schemas explícitos e testes.
- Reproducible containers: Dockerfiles, Compose, versões e caminhos de volumes serão explícitos; modelos e resultados não entram na imagem.
- Test-first quality: cada contrato novo terá testes de validação, sucesso, erro e streaming; Compose terá validação/smoke.
- Safe operations: credenciais remotas não serão persistidas, fallback remoto será opt-in e logs não conterão payload completo.

## Project Structure

```text
app/
├── services/
│   ├── api/
│   │   ├── pyproject.toml
│   │   ├── Dockerfile
│   │   ├── README.md
│   │   ├── src/local_llm/
│   │   │   ├── core/              # contracts and provider-neutral types
│   │   │   ├── application/      # generation and model selection use cases
│   │   │   ├── infrastructure/   # OVMS HTTP adapter
│   │   │   ├── api/              # FastAPI schemas/routes
│   │   │   ├── cli.py
│   │   │   └── main.py
│   │   └── tests/
│   └── benchmark/
│       ├── Dockerfile
│       ├── pyproject.toml
│       ├── src/benchmark_runner/
│       ├── tests/
│       └── results/               # runtime-owned, ignored
├── deploy/
│   ├── compose.yaml
│   └── .env.example
├── models/                         # local model cache, ignored
├── scripts/                        # model preparation and local helpers
└── README.md
```

The shared Git root remains the owner of `harness/` and `app/`; no new
repository is introduced. The current `openvino_models_server` namespace is
migrated to `local_llm` inside the API package. A small compatibility shim can
remain during the migration if existing imports require it, but public
contracts use provider-neutral names.

## Design Decisions

1. Use a provider protocol and immutable request/response contracts. The API,
   CLI and benchmark depend on contracts, while OVMS is an adapter.
2. Keep Docker/OVMS as the server runtime and make a direct native runtime a
   future adapter; this avoids coupling package installation to Docker today.
3. Use the standard OpenAI Chat Completions wire contract for interoperability.
   LangChain can initially use its OpenAI integration with a custom base URL;
   its provider-specific adapter remains optional.
4. Keep benchmark execution in its own service and its reports beside that
   service. The API may submit/query jobs but does not own runner code or
   report files.
5. Keep the 1.7B default and add explicit runtime knobs for output limits,
   concurrency and 8B scheduler experiments. Do not regenerate or replace
   model weights in this feature.

## Migration and Compatibility

- Preserve `/v1/generate/sync`, `/v1/generate/async`, `/v1/generate/stream`,
  `/v1/models`, `/healthz`, `/readyz` and benchmark routes.
- Add `/v1/chat/completions` and map its messages to the existing generation
  service without duplicating provider I/O.
- Move Compose paths and mounts atomically; keep model directory contents and
  report formats stable.
- Update documentation and tests to use the new paths, then remove only dead
  root-level service files after the moved paths pass validation.

## Complexity Tracking

| Added structure | Why needed | Simpler alternative rejected because |
|---|---|---|
| Separate API and benchmark service directories | They have different dependencies, lifecycles and output ownership | Keeping both at the root caused divergent changes and mixed runtime artifacts |
| Provider-neutral core contracts | Enables OVMS now and LangChain/OpenAI-compatible use without coupling | Exposing OVMS client types would make future providers and tests depend on infrastructure |
| Optional LangChain integration boundary | LangChain is a consumer, not a core dependency | Making LangChain mandatory would enlarge install size and couple the package to one ecosystem |
