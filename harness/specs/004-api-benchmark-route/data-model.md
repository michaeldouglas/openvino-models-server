# Data model: benchmark administrativo

## BenchmarkSpec

Entrada validada para uma execução: `model`, `prompt_tokens`, `output_tokens`,
`concurrency`, `max_requests` e `max_duration_seconds`. Todos os números têm
limites fechados no contrato; `model` pertence ao catálogo configurado.

## BenchmarkJob

- `run_id`: identificador seguro e único.
- `model`: alias selecionado.
- `status`: `running`, `completed` ou `failed`.
- `results_path`: caminho lógico dentro de `/results`.
- `files`: formatos realmente produzidos.
- `successful_requests`, `errored_requests`: contagens quando disponíveis.
- `error`: mensagem pública somente em falha.
- `created_at`, `finished_at`: timestamps ISO-8601 opcionais.

Estados:

```text
running -> completed
running -> failed
```

Um job não volta para `running`, não é reutilizado para outra execução e não
permite acessar arquivos de outro `run_id`.

## BenchmarkReport

Um dos arquivos `benchmarks.json`, `benchmarks.csv` ou `benchmarks.html`,
resolvido exclusivamente sob a pasta do próprio job.
