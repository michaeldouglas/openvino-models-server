# Implementation Plan: Exemplo HTML de chat

**Branch**: `feature/html-chat-example`

## Design

- `index.html` será um frontend estático sem dependências de build.
- Nginx servirá a página e fará proxy de `/api/*` para a API local em
  `host.docker.internal:8000`.
- `compose.yaml` conterá somente o serviço do exemplo e montará os dois
  arquivos estáticos como somente leitura.
- O frontend consumirá `/api/v1/models` no carregamento e escolherá entre
  `/api/v1/generate/sync`, `/api/v1/generate/async` e
  `/api/v1/generate/stream` no envio.

## Validation

- Validar YAML com `docker compose config -q`.
- Subir o exemplo isoladamente e verificar HTTP 200 na página.
- Verificar a rota proxied de modelos.
- Validar que o README contém os comandos mínimos solicitados.
