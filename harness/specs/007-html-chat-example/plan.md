# Implementation Plan: Exemplo HTML de chat

**Branch**: `feature/test-complete-stack`

## Design

- `index.html` será um frontend estático sem dependências de build.
- Nginx servirá a página e fará proxy de `/api/*` para o serviço `api` na rede
  Compose compartilhada.
- O Compose principal terá um perfil opcional `chat-example` que monta os dois
  arquivos estáticos como somente leitura e mantém o exemplo na mesma rede da
  API.
- O frontend consumirá `/api/v1/models` no carregamento e escolherá entre
  `/api/v1/generate/sync`, `/api/v1/generate/async` e
  `/api/v1/generate/stream` no envio.

## Validation

- Validar YAML com `docker compose config -q`.
- Subir o perfil `chat-example` e verificar HTTP 200 na página.
- Verificar a rota proxied de modelos.
- Validar que o README contém os comandos mínimos solicitados.
