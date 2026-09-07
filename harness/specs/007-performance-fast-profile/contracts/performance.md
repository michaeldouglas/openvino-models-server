# Performance Contract

Performance instrumentation is additive and must not change the existing JSON
response schemas for `/v1/generate/sync`, `/v1/generate/async`,
`/v1/generate/stream`, or `/v1/chat/completions`.

The service may expose timing metadata through structured logs and internal
benchmark reports. These fields are allowed:

```json
{
  "profile": "fast",
  "request_id": "request-id",
  "model": "qwen3-1.7b",
  "streaming": true,
  "ttft_ms": 420.1,
  "total_latency_ms": 3850.4,
  "output_tokens": 32,
  "output_tokens_per_second": 8.3,
  "outcome": "success"
}
```

The contract forbids full prompt and response text in performance logs or
persistent benchmark metadata. Existing public error codes and model aliases
remain unchanged.
