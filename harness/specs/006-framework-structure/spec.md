# Feature Specification: Estrutura de pacotes e runtime do framework

**Feature Branch**: `feature/reorganize-framework-structure`

**Created**: 2026-09-07

**Status**: Draft

**Input**: Reorganizar a árvore do framework para que pacotes instaláveis,
runtime/deployment, modelos e benchmark tenham ownership explícito sem deixar
diretórios de infraestrutura espalhados na raiz de `app`.

## User Stories & Testing

### User Story 1 - Entender o produto pela árvore (Priority: P1)

Como mantenedor, quero identificar rapidamente o pacote principal, o benchmark
e os artefatos de execução sem navegar por diretórios genéricos.

**Independent Test**: a árvore de `app` deve ter apenas grupos de produto
(`packages`, `runtime`, `examples`) e o README deve apontar cada ownership.

### User Story 2 - Preservar instalação e execução (Priority: P1)

Como usuário, quero manter os comandos de instalação, CLI, Docker Compose e
contratos HTTP depois da reorganização.

**Independent Test**: testes da API e benchmark, instalação editável, CLI e
`docker compose config -q` passam usando somente os novos caminhos.

### User Story 3 - Tornar as camadas internas explícitas (Priority: P2)

Como desenvolvedor, quero distinguir `core`, casos de uso, adapters e
interfaces para adicionar providers sem misturar HTTP com regras de negócio.

**Independent Test**: o pacote `local_llm.core` não importa FastAPI, HTTPX,
OVMS ou LangChain; o adapter OVMS fica isolado da interface HTTP.

## Edge Cases

- Modelos locais existentes devem ser preservados durante a mudança de caminho.
- Resultados existentes de benchmark não podem ser apagados nem versionados.
- `.env` local continua funcionando ou recebe uma migração documentada.
- Imports, entry point `local-llm` e comandos Compose não podem apontar para a
  antiga árvore `services`/`deploy`.
- O benchmark não pode depender de módulos privados do pacote da API.

## Requirements

- **FR-001**: O código distribuível MUST ficar em `app/packages/local-llm`.
- **FR-002**: O benchmark MUST ficar em `app/packages/benchmark-runner`.
- **FR-003**: Deployment, modelos e scripts MUST ficar agrupados sob
  `app/runtime`.
- **FR-004**: `local_llm.core` MUST conter contratos sem dependência de
  transporte ou provider.
- **FR-005**: A mudança MUST preservar o comportamento público da API, CLI,
  benchmark e instalação editável.
- **FR-006**: Caminhos de modelos, cache, resultados, Dockerfiles e Compose
  MUST ser atualizados para a nova árvore.
- **FR-007**: Nenhum peso, segredo, cache ou resultado gerado MUST entrar no
  commit.
- **FR-008**: A documentação MUST explicar a separação entre pacote,
  runtime, exemplos e benchmark.

## Success Criteria

- **SC-001**: A raiz de `app` fica limitada a `packages`, `runtime`,
  `examples` e documentação/configuração mínima.
- **SC-002**: API e benchmark passam todos os testes existentes sem alterar
  seus contratos públicos.
- **SC-003**: Compose, CLI e instalação editável funcionam sem referências aos
  caminhos antigos.
- **SC-004**: Modelos e resultados locais permanecem acessíveis nos novos
  diretórios e continuam ignorados pelo Git.

## Assumptions

- A feature é uma refatoração estrutural e não adiciona providers novos.
- O namespace Python `local_llm` e o comando `local-llm` permanecem públicos.
- O `.env` de desenvolvimento pode continuar na raiz de `app` para manter a
  compatibilidade; o exemplo de configuração pertence ao runtime.
