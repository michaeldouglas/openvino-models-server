# Implementation Plan: OpenVINO Model Server API

**Branch**: `feature/implement-openvino-models-server` | **Date**: 2026-09-06
| **Spec**: `specs/001-fastapi-openvino-inference/spec.md`

**Implementation target**: `C:/Users/mdbaa/development/Agents/server-agents/app`

## Summary

Implementar uma API FastAPI pequena e tipada que delega geração ao OVMS pela
rede privada do Docker Compose. O FastAPI terá adaptadores sync e async para o
mesmo contrato de inferência, e um adaptador de streaming que encaminha os SSE
do OVMS. O modelo será carregado exclusivamente pelo serviço `ovms`, em volume
persistente, com `--target_device GPU` explícito.

## Technical Context

**Language/Version**: Python 3.13 (compatível com `.python-version` existente)

**Primary Dependencies**: FastAPI 0.116.x, Pydantic 2.11.x,
pydantic-settings 2.10.x, httpx 0.28.x, Uvicorn 0.35.x; pytest 8.4.x,
pytest-cov 6.2.x e ruff 0.12.x em desenvolvimento.

**Inference**: OpenVINO Model Server `openvino/model_server:2026.3.1-gpu`,
OpenAI-compatible `/v1/chat/completions`, modelo inicial
`OpenVINO/Qwen3-1.7B-int4-ov`. A versão e digest da imagem serão confirmados
antes do primeiro pull; nenhuma compatibilidade GPU é presumida.

**Storage**: `app/models/` persistente e ignorado; o OVMS monta esse diretório
como `/models`. A API não recebe nem persiste pesos.

**Testing**: pytest com `TestClient`, `httpx.MockTransport`/fakes de provider,
contrato OpenAPI, parsing SSE, timeout, erro e concorrência limitada. Smoke
Docker e geração real são validações separadas e dependem do ambiente.

**Target Platform**: Docker Desktop Linux VM no Windows 11; GPU Intel exige
WSL2 e acesso `/dev/dxg` mais `/usr/lib/wsl` conforme a documentação oficial.

**Project Type**: serviço web HTTP com servidor de inferência interno.

**Performance Goals**: medir TTFT, latência total, tokens/s quando informado,
startup/compilação, primeira chamada, aquecimento e concorrência pequena. Não
há meta arbitrária sem medição real.

**Constraints**: API publicada em `127.0.0.1`; OVMS sem porta publicada por
padrão; carregamento único no OVMS; sem histórico, filas, retry automático,
fallback CPU, secrets versionados ou dependência do harness.

**Scale/Scope**: uma instância de API e uma de OVMS; limite de concorrência
configurável e conservador; sem autenticação pública, persistência de conversa,
frontend ou serviços auxiliares.

## Constitution Check

### Before Phase 0

- **Skills-First**: PASS. Hardware, documentação OVMS, API, Docker, tipagem,
  testes e revisão serão aplicados conforme seus `SKILL.md`; os resultados
  parciais do host já registram OpenVINO ausente e Docker sem GPU validada.
- **Explicit FastAPI Contracts**: PASS. O OpenAPI e schemas tipados precedem
  as rotas.
- **Reproducible Containerization**: PASS with evidence pending. A imagem é
  versionada; o digest e o acesso GPU ainda precisam de confirmação operacional.
- **Test-First Quality**: PASS. Testes controlados acompanham cada rota e erro;
  smoke e modelo real ficam como gates separados.
- **Observable and Safe Operations**: PASS. Readiness não gera texto e logs
  minimizam payloads.

### Post-Design

- **Skills-First**: PASS. A recomendação Qwen3-1.7B INT4 é explicitamente
  provisória e não substitui validação de modelo, GPU ou desempenho.
- **Explicit FastAPI Contracts**: PASS. Todas as três rotas compartilham
  request/result mapping e têm contrato SSE documentado.
- **Reproducible Containerization**: PASS with runtime evidence pending. O
  Compose fixa imagem, volumes e comando; a configuração de host continua uma
  pré-condição verificável.
- **Test-First Quality**: PASS. Implementação deve seguir testes controlados e
  não mascarar falhas de integração real.
- **Observable and Safe Operations**: PASS. Erros upstream são traduzidos,
  disconnect fecha recursos e readiness consulta capacidade sem inferência.

## Project Structure

```text
app/
├── src/openvino_models_server/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── application/
│   │   └── generation.py
│   └── infrastructure/
│       ├── errors.py
│       └── ovms_client.py
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_ovms_client.py
│   └── test_sse.py
├── Dockerfile
├── compose.yaml
├── .env.example
├── pyproject.toml
├── README.md
└── models/.gitkeep
```

O contrato interno é um protocolo pequeno (`InferenceProvider`) implementado
por um adaptador OVMS. A escolha é composição e injeção explícita, suficiente
para isolar I/O e permitir testes; não haverá fábrica ou camada vazia. Sync usa
`httpx.Client` em dependência executada por threadpool do FastAPI; async usa
`httpx.AsyncClient`; stream usa `StreamingResponse` e fecha o response upstream
em `finally`.

## Phases

1. **Foundation**: dependências, configuração validada, schemas, erros,
   protocolo, clientes OVMS e lifecycle de clientes.
2. **Generation**: rotas sync/async/stream, limite de concorrência, parsing
   OpenAI-compatible, SSE e readiness.
3. **Platform**: Dockerfile, Compose API+OVMS, `.env.example`, volume de modelo,
   configuração GPU WSL2 somente quando evidenciada, e documentação.
4. **Quality**: testes permanentes, contrato OpenAPI, lint/tipagem, revisão
   independente, Graphify do app e relatório da execução.
5. **Runtime gate**: pull/preparação idempotente, startup e geração reais no
   OVMS/GPU; se bloqueado, registrar exatamente a pré-condição restante.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Dois serviços Compose | O usuário exige API separada do carregamento OVMS/GPU | Carregar modelo no FastAPI quebraria o isolamento e duplicaria pesos |
| Dois clientes HTTP | Sync e async têm requisitos de I/O diferentes | Usar cliente sync em `async def` bloquearia o event loop |
