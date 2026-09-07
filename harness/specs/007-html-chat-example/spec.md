# Feature Specification: Exemplo HTML de chat

**Feature Branch**: `feature/html-chat-example`

## Objetivo

Entregar um exemplo visual mínimo para testar o framework no navegador sem
configurar um frontend separado.

## Requisitos

- **FR-001**: O exemplo MUST ficar em `app/examples/chat-html`.
- **FR-002**: O exemplo MUST listar modelos prontos usando `/v1/models`.
- **FR-003**: O exemplo MUST permitir chamadas `sync`, `async` e `streaming`
  pelas rotas `/v1/generate/sync`, `/v1/generate/async` e
  `/v1/generate/stream`.
- **FR-004**: O exemplo MUST ser executável com `docker compose up -d` dentro
  da própria pasta.
- **FR-005**: O proxy MUST evitar dependência de CORS no navegador.
- **FR-006**: O README MUST conter somente o caminho, comando de execução,
  URL e comando de parada essenciais.

## Critérios de aceite

- A página abre em `http://127.0.0.1:8088`.
- Modelos com status `ready` aparecem no seletor.
- Uma mensagem retorna texto nas modalidades sync, async e streaming.
- `docker compose down` remove o container do exemplo sem afetar a API.
