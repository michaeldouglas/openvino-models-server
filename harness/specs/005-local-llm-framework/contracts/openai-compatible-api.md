# Contract: OpenAI-compatible local chat API

## `GET /v1/models`

Returns available model aliases and readiness.

```json
{
  "object": "list",
  "data": [
    {"id": "qwen3-1.7b", "object": "model", "owned_by": "local-llm"}
  ]
}
```

The implementation may include readiness metadata in additive fields. Model
selection remains per request.

## `POST /v1/chat/completions`

Request fields required for the MVP:

```json
{
  "model": "qwen3-1.7b",
  "messages": [
    {"role": "system", "content": "Responda de forma objetiva."},
    {"role": "user", "content": "O que é OpenVINO?"}
  ],
  "temperature": 0.2,
  "max_tokens": 64,
  "stream": true
}
```

Rules:

- `model` must be a ready configured alias.
- `messages` must contain at least one user or assistant-compatible message.
- `max_tokens` and input length are bounded by service configuration.
- `stream=false` returns one OpenAI-compatible response with one assistant
  choice.
- `stream=true` returns `text/event-stream` data chunks followed by `[DONE]`.
- Invalid model, validation, capacity and upstream errors use an `error` object
  with a request ID and no stack trace.
- API keys are not required for the local-only MVP; a local compatibility key
  may be accepted but is not logged or forwarded to OVMS.

## Compatibility

The existing `/v1/generate/sync`, `/v1/generate/async` and
`/v1/generate/stream` routes remain supported during migration.
