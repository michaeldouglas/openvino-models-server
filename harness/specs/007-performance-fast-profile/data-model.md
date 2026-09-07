# Data Model: Performance Profile

## PerformanceProfile

Represents a named runtime configuration selected by deployment.

| Field | Type | Rules |
|---|---|---|
| name | string | `fast` or `quality` in the initial deployment |
| default_model | string | Must be listed among enabled models |
| enabled_models | list[string] | Must contain at least one prepared model |
| max_concurrency | integer | Positive and within the API-supported range |
| max_num_seqs | integer | Positive and compatible with the selected model graph |
| device | string | Initial profiles use `GPU` with the existing Docker device mapping |
| cache_enabled | boolean | True for the supported profiles |

## GenerationMeasurement

An in-memory/request-level observation used by logs and benchmark reports.

| Field | Type | Rules |
|---|---|---|
| request_id | string | Must not contain prompt content |
| model | string | Resolved model alias |
| profile | string | Named deployment profile |
| streaming | boolean | Indicates the selected response mode |
| concurrency | integer | Active capacity at measurement time |
| ttft_ms | number or null | Set when the first stream chunk is observed |
| total_latency_ms | number | Set on successful completion or failure |
| output_tokens | integer or null | Taken from provider usage when available |
| output_tokens_per_second | number or null | Derived only when token count and duration exist |
| outcome | string | `success`, `timeout`, `capacity`, or `upstream_error` |

Measurements are operational metadata. Prompt and full response content are not
part of the persisted report.
