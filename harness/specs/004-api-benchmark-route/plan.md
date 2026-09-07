# Implementation Plan: Execução de benchmarks pela API

**Branch**: `feature/api-benchmark-route` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

## Summary

Adicionar um contrato administrativo assíncrono à API para iniciar, consultar e
baixar relatórios de benchmarks. A API será apenas o gateway HTTP; um serviço
executor separado, construído sobre a imagem fixada do GuideLLM, executará o
processo e escreverá em `app/results/`, que ficará ignorado pelo Git. O socket
do Docker não será montado no FastAPI.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI 0.116.x, httpx 0.28.x, Pydantic Settings 2.10.x, GuideLLM 0.7.3
**Storage**: filesystem local configurável; estado de jobs em memória no executor
**Testing**: pytest, TestClient/httpx com gateway fake, testes unitários do executor
**Target Platform**: Docker Compose em Windows/WSL2 ou Linux
**Project Type**: API FastAPI com serviço interno de operação
**Performance Goals**: aceitar a solicitação sem aguardar a geração; rejeitar nova execução quando o limite do executor estiver ocupado
**Constraints**: catálogo e limites allowlisted; somente JSON/CSV/HTML; sem fila ilimitada, Docker socket, segredo ou prompt completo em respostas/logs
**Scale/Scope**: uma execução ativa por padrão; estado não sobrevive à reinicialização, arquivos concluídos permanecem

## Constitution Check

| Principle | Status | Evidence |
|---|---|---|
| Skills-First Implementation | PASS | FastAPI, Docker, tipagem, testes e design-patterns foram lidos e aplicados; decisões registradas aqui. |
| Explicit FastAPI Contracts | PASS | Schemas tipados, `202`, status, relatório e erros documentados em `contracts/`. |
| Reproducible Containerization | PASS | Executor usa imagem GuideLLM por tag e digest; dependências do executor são fixadas. |
| Test-First Quality | PASS | Testes de contrato, validação, falhas e isolamento serão adicionados antes da validação final. |
| Observable and Safe Operations | PASS | Estados, logs por execução, limites, readiness e respostas sem stack trace. |

## Architecture

```text
client -> FastAPI /v1/benchmarks -> benchmark-runner:8080
                                      | subprocess GuideLLM
                                      v
                                  OVMS :8000
                                      |
                         app/results/<run-id>/{json,csv,html}
```

O gateway mantém apenas um cliente HTTP reutilizável para o executor. O
executor valida novamente o catálogo, cria o identificador, inicia um
subprocesso assíncrono e expõe somente recursos internos. O download de
relatório usa uma allowlist de extensões e validação do caminho resolvido.

## Project Structure

- `app/src/openvino_models_server/api/schemas.py`: contratos públicos dos jobs.
- `app/src/openvino_models_server/api/routes.py`: endpoints públicos de criação, status e relatório.
- `app/src/openvino_models_server/infrastructure/benchmark_client.py`: gateway HTTP assíncrono para o executor.
- `app/src/openvino_models_server/application/benchmarking.py`: DTOs e protocolo pequeno do gateway.
- `app/src/openvino_models_server/main.py`: ciclo de vida do cliente do executor.
- `app/benchmark_runner/server.py`: serviço interno e execução controlada do GuideLLM.
- `app/benchmark_runner/Dockerfile`: imagem do executor sem alterar a imagem da API.
- `app/compose.yaml`: serviço `benchmark-runner` sob o profile `benchmark-api`.
- `app/results/`: saída local ignorada; não é dependência do código versionado.
- `app/tests/`: testes permanentes de contrato e integração controlada.

## Design Decisions

1. **Job assíncrono**: evita manter uma conexão HTTP aberta durante o benchmark.
2. **Executor separado**: impede que o FastAPI execute shell/Docker e mantém o
   GuideLLM fora das dependências de produção da API.
3. **Memória + filesystem**: é proporcional ao uso local atual; não introduz
   Redis/banco antes de existir requisito de durabilidade distribuída.
4. **Allowlist dupla**: a API valida o contrato e o executor valida novamente
   modelo, formato de relatório e limites antes de iniciar processo.
5. **Composição simples**: um gateway HTTP injetável permite testes sem Docker;
   não são adicionadas fábricas ou camadas sem responsabilidade concreta.

## Risks and Mitigations

- Reinício perde o estado em memória: status retorna não encontrado, enquanto
  artefatos já escritos continuam no volume; persistência fica para outra feature.
- Serviço executor indisponível: o gateway retorna erro seguro `503`.
- Relatório incompleto: o executor marca falha se os três arquivos não existirem
  ou se o JSON não registrar requisição bem-sucedida.
- Recursos consumidos por jobs: limite de uma execução ativa e limites de
  entrada/saída/duração; sem fila ilimitada.
