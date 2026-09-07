# Data Model: Framework local de LLMs

## ModelManifest

Represents an installable model artifact.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Stable identifier used by the model manager |
| `alias` | string | Unique request-facing name |
| `source` | string | Approved source/repository reference |
| `revision` | string | Immutable or explicitly recorded revision |
| `precision` | string | For example `int4` |
| `license` | string | Required before distribution |
| `devices` | list[string] | Supported device names |
| `path` | path | Local cache path, never packaged with the wheel |
| `sha256` | string | Required for managed downloads |

## ChatRequest

Provider-neutral generation input: messages, selected alias, maximum output,
temperature, stream flag and optional provider-safe parameters.

Validation: messages are non-empty; model aliases are validated before provider
dispatch; output and input limits come from settings; unknown public fields are
rejected unless explicitly placed in an extension field.

## ChatResponse and ChatChunk

`ChatResponse` is a completed assistant message with model, finish reason and
optional usage. `ChatChunk` is an incremental text delta followed by a terminal
chunk. Both carry request correlation but never full secrets or raw credentials.

## ProviderConfig

Describes a local or remote backend without embedding credentials. The provider
name, endpoint, model alias, device and explicit fallback policy are public
configuration; API keys arrive from the process environment or secret store.

## BenchmarkRun

Represents a measurement job with run ID, model, prompt/output token targets,
concurrency, duration/request limits, status, result file names, success/error
counts and metrics. Its files are owned by `services/benchmark/results`.

## Relationships

- One `ModelManifest` can be referenced by one or more `ModelAlias` values only
  when aliases are intentionally distinct.
- A `ChatRequest` resolves to exactly one provider configuration and model alias.
- A `BenchmarkRun` resolves one model alias and one immutable workload profile.
- API adapters map transport schemas to these provider-neutral entities.
