# Data Model: FastAPI OpenVINO Text Inference

## GenerationRequest

Representa uma solicitação de geração enviada pelo consumidor.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `text` | string | yes | Must not be empty or whitespace-only; length must be at or below the configured limit. |

The MVP does not accept conversation history, files, images, streaming options
or model-selection fields from the consumer.

## GenerationResult

Representa o resultado funcional da solicitação.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `text` | string | yes | Generated text returned by the configured model; may be empty only if the selected model contract explicitly permits it. |

The response does not expose model paths, credentials, internal device details or
full diagnostic traces.

## ModelConfiguration

Configuração interna fornecida pelo ambiente de execução.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `model_reference` | string/path | yes | Points to a model supplied outside the application image. |
| `device` | string | yes | Explicitly configured OpenVINO device profile; initial planning default is `CPU`. |
| `max_input_length` | positive integer | yes | Requests above this value are rejected before inference. |
| `request_timeout_seconds` | positive number | yes | Generation exceeding this value ends with a controlled timeout. |

The configuration is validated at startup. Invalid required configuration prevents
readiness and produces a safe operator-facing reason.

## ReadinessState

Estado operacional do serviço.

| State | Meaning | Transition trigger |
|---|---|---|
| `starting` | Process is starting and model readiness is not known. | Process startup begins. |
| `ready` | Configuration and model are available for generation. | Model loading/validation completes successfully. |
| `not_ready` | Process is alive but cannot safely generate text. | Missing/invalid configuration, unavailable model or load failure. |
| `stopping` | Process is shutting down and must not accept new work. | Shutdown begins. |

## ErrorResponse

Formato seguro e estável para erros.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `error.code` | enum string | yes | Stable category such as `invalid_request`, `not_ready`, `model_unavailable`, `generation_timeout` or `generation_failed`. |
| `error.message` | string | yes | Actionable, non-sensitive message for the consumer. |
| `error.request_id` | string | yes | Correlation identifier safe to include in logs and support communication. |

## OperationalEvent

Registro estruturado para operação e diagnóstico.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `timestamp` | timestamp | yes | Event time. |
| `event` | enum string | yes | Startup, readiness, request failure, generation failure or shutdown. |
| `request_id` | string | conditional | Present for request-scoped events. |
| `error_code` | string | conditional | Present when the event represents a failure. |
| `duration_ms` | non-negative number | conditional | Present for completed or timed-out generation. |

Operational events MUST NOT contain credentials, full prompts, full generated
responses or personal paths.
