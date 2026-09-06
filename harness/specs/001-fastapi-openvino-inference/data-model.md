# Data Model: OpenVINO Model Server API

## GenerationRequest

`text` obrigatório, não vazio e limitado por `MAX_INPUT_CHARS` (default 12.000).
`max_tokens` default 128, intervalo 1–512. `temperature` default 0,2,
intervalo 0–2. O request não aceita modelo, URL, caminho, histórico ou system
prompt do cliente.

## GenerationResponse

`request_id`, `model`, `text` e `finish_reason` obrigatórios. `usage` é opcional
e só aparece quando o OVMS realmente fornece o objeto.

## StreamEvent

Evento SSE com `event: delta|done|error` e `data` JSON. `delta` possui texto
incremental e request/model quando disponíveis; `done` possui finish reason e
request ID; `error` possui código, mensagem segura e request ID. O consumidor
reconstrói a resposta concatenando somente os deltas.

## InferenceProvider

Contrato interno com `generate_sync`, `generate_async`, `stream` e `readiness`.
Ele recebe apenas request já validado e configuração interna; não aceita
seleção de modelo do cliente.

## RuntimeConfiguration

Endpoint interno do OVMS, nome do modelo, timeout, limite de entrada, limite de
geração, limite de concorrência e modelo esperado. O dispositivo esperado é
`GPU` no OVMS; a API não inventa informação de dispositivo.

## ErrorResponse

Objeto `error` com `code`, `message` e `request_id`. Códigos: `invalid_request`,
`capacity_limited`, `not_ready`, `upstream_unavailable`, `upstream_failed` e
`generation_timeout`. Stack traces, credenciais, prompts e respostas completas
ficam fora do contrato.
