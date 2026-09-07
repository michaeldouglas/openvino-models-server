# Implementation Plan: Seleção entre modelos Qwen

**Branch**: `feature/multi-model-qwen-selection` | **Date**: 2026-09-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `harness/specs/002-multi-model-qwen-selection/spec.md`

## Summary

Adicionar seleção segura de modelo às três rotas existentes e um catálogo operacional para Qwen3-1.7B e Qwen3-8B. O FastAPI continuará sem pesos ou OpenVINO local; o OVMS será iniciado com configuração para múltiplos servables. Os modelos serão preparados separadamente em `app/models`, com o 1.7B como padrão e fallback.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, Pydantic, httpx, OVMS 2026.3.1 GPU image
**Storage**: filesystem persistente `app/models`; configuração operacional gerada no repositório de modelos
**Testing**: pytest, httpx MockTransport/TestClient, Ruff, mypy
**Target Platform**: Windows 11 + Docker Desktop/WSL2 com Intel Arc 140V; Linux compatível documentado separadamente
**Project Type**: serviço web FastAPI com servidor de inferência externo
**Performance Goals**: preservar latência do modelo padrão e medir o 8B com concorrência 1 antes de aumentar limites
**Constraints**: API não baixa no boot, não aceita caminho/URL de modelo do cliente, memória compartilhada limitada, GPU explícita
**Scale/Scope**: dois modelos Qwen, seleção por requisição, catálogo/readiness; download dinâmico fica fora desta feature

## Constitution Check

- I. Skills-First: PASS — FastAPI, Docker, type safety, testing, design patterns e OVMS foram consultados.
- II. Explicit Contracts: PASS — `model` opcional e catálogo serão documentados no OpenAPI.
- III. Reproducible Containerization: PASS — image tag existente e preparação separada; artefatos ficam fora da imagem.
- IV. Test-First Quality: PASS — adicionar testes de seleção, catálogo e regressão antes da implementação.
- V. Observable and Safe Operations: PASS — estados seguros, sem logs de prompts/tokens; falhas do upstream permanecem explícitas.

## Project Structure

```text
app/
├── compose.yaml                         # OVMS em config.json e volume de modelos
├── .env.example                         # aliases, default e limites
├── scripts/prepare-models.ps1           # preparação idempotente fora do boot
├── src/openvino_models_server/
│   ├── api/routes.py                    # seleção e catálogo HTTP
│   ├── api/schemas.py                   # contratos
│   ├── application/generation.py       # validação e resolução do alias
│   ├── config.py                        # catálogo configurável
│   └── infrastructure/ovms_client.py  # payload por modelo e status
└── tests/                               # testes permanentes

harness/specs/002-multi-model-qwen-selection/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/openapi.yaml
└── tasks.md
```

**Structure Decision**: manter as camadas atuais e introduzir apenas um catálogo pequeno, injetado no serviço de geração. Não criar fábrica genérica, banco, fila ou novo servidor.

## Design decisions

- O alias é resolvido na camada de aplicação; o cliente OVMS recebe somente o servable já validado.
- `OVMSClient` mantém clientes HTTP compartilhados e apenas troca o campo `model` do payload.
- `/v1/models` consulta o upstream sem gerar texto. `/readyz` continua representando a disponibilidade do modelo padrão.
- O Compose usa `config.json` montado de `app/models`; a preparação gera/atualiza esse arquivo de forma idempotente.
- O stream captura o alias resolvido antes de iniciar os headers para que eventos `delta`, `done` e `error` tenham o modelo correto.

## Complexity Tracking

Nenhuma violação constitucional planejada. O catálogo é uma abstração necessária porque há dois modelos e três rotas consumidoras; uma variável global seria menos segura.
