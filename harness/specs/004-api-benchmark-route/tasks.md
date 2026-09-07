# Tasks: Execução de benchmarks pela API

## Phase 1: Setup

- [x] T001 Atualizar `app/compose.yaml`, `app/.dockerignore` e o root `.gitignore` para o executor e resultados locais.
- [x] T002 [P] Criar `app/benchmark_runner/Dockerfile` com imagem GuideLLM digestada e dependências do serviço interno fixadas.
- [x] T003 [P] Criar `app/src/openvino_models_server/application/benchmarking.py` com DTOs e protocolo injetável.

## Phase 2: Foundational

- [x] T004 Adicionar configuração do executor em `app/src/openvino_models_server/config.py` e ciclo de vida em `app/src/openvino_models_server/main.py`.
- [x] T005 Criar erros públicos de benchmark em `app/src/openvino_models_server/infrastructure/errors.py`.
- [x] T006 [P] Criar testes de contrato fake em `app/tests/test_api.py` antes do gateway real.

## Phase 3: User Story 1 - Solicitar medição

- [x] T007 [US1] Adicionar schemas de benchmark em `app/src/openvino_models_server/api/schemas.py`.
- [x] T008 [US1] Implementar `app/src/openvino_models_server/infrastructure/benchmark_client.py` com HTTP async reutilizável.
- [x] T009 [US1] Adicionar POST `/v1/benchmarks` e injeção do gateway em `app/src/openvino_models_server/api/routes.py`.
- [x] T010 [US1] Implementar submissão e limite de execução em `app/benchmark_runner/server.py`.

## Phase 4: User Story 2 - Consultar relatórios

- [x] T011 [US2] Implementar GET de status e relatório no gateway e nas rotas em `app/src/openvino_models_server/infrastructure/benchmark_client.py` e `app/src/openvino_models_server/api/routes.py`.
- [x] T012 [US2] Implementar validação segura de `run_id`, formatos e arquivos no `app/benchmark_runner/server.py`.
- [x] T013 [US2] Adicionar testes de status, relatório, formato inválido e job inexistente em `app/tests/test_api.py`.

## Phase 5: User Story 3 - Segurança e repetibilidade

- [x] T014 [US3] Adicionar testes do comando GuideLLM, allowlist, limites, isolamento de diretórios e falhas em `app/tests/test_benchmark_runner.py`.
- [x] T015 [US3] Registrar manifesto/log por execução e estados seguros no `app/benchmark_runner/server.py`.
- [x] T016 [US3] Validar que a execução real exige OVMS acessível e marca falhas sem relatório completo no `app/benchmark_runner/server.py`.

## Phase 6: User Story 4 - Preservar geração

- [x] T017 [US4] Atualizar `app/tests/test_api.py` para confirmar que as rotas de geração e OpenAPI existentes permanecem compatíveis.
- [x] T018 [US4] Atualizar `app/README.md` com o modo de inicialização, contrato, pasta de resultados e limitações.

## Phase 7: Polish and validation

- [x] T019 Executar pytest, Ruff, mypy e validação do Compose, direcionando saídas ao runner do harness quando aplicável.
- [x] T020 Construir e iniciar o executor no Compose, executar um benchmark curto real e registrar o resultado em `app/results/` sem commitá-lo.
- [x] T021 Atualizar Graphify no diretório `app` e registrar a evidência em `harness/.agent-work`.

## Dependencies

`T001`-`T005` precedem as histórias. `US1` precede `US2`; `US3` pode testar
componentes do executor após `T010`; `US4` valida regressão após as rotas. T019
e T020 são gates finais.

## MVP

O MVP é `US1` + `US2`: criar job, executar GuideLLM isolado e consultar os três
relatórios. Segurança, regressão e validação real são obrigatórias antes de
considerar a feature concluída.
