# Quickstart: benchmark pela API

## Subir a stack com o executor

A partir de `app` no PowerShell:

```powershell
docker compose --profile benchmark-api up -d --build
docker compose ps
curl.exe http://127.0.0.1:8000/healthz
```

O `benchmark-runner` não publica porta no host. A API acessa o executor pelo
hostname interno `benchmark-runner`. A pasta `app/results/` será criada ou
reutilizada e não deve ser commitada.

## Criar uma execução

```powershell
$body = '{"model":"qwen3-8b","prompt_tokens":32,"output_tokens":32,"concurrency":1,"max_requests":1}'
curl.exe -X POST http://127.0.0.1:8000/v1/benchmarks `
  -H "Content-Type: application/json" -d $body
```

Guarde o `run_id` retornado. O endpoint responde `202`; isso significa que o
processo foi aceito e não que o relatório já terminou.

## Consultar e abrir o resultado

```powershell
$runId = '<run-id>'
curl.exe http://127.0.0.1:8000/v1/benchmarks/$runId
curl.exe -o "app-results-$runId.html" `
  "http://127.0.0.1:8000/v1/benchmarks/$runId/report?format=html"
Start-Process ".\app-results-$runId.html"
```

Para inspeção local direta, os arquivos estarão em:

```text
app/results/<run-id>/benchmarks.json
app/results/<run-id>/benchmarks.csv
app/results/<run-id>/benchmarks.html
app/results/<run-id>/run.log
```

O JSON/HTML continua sendo a fonte das métricas do GuideLLM. O benchmark mede
OVMS diretamente; não representa a latência adicional da rota FastAPI.

## Limites e concorrência

```powershell
curl.exe -X POST http://127.0.0.1:8000/v1/benchmarks `
  -H "Content-Type: application/json" `
  -d '{"model":"qwen3-1.7b","prompt_tokens":16,"output_tokens":16,"concurrency":1,"max_requests":2,"max_duration_seconds":30}'
```

O executor rejeita uma segunda execução enquanto a capacidade configurada
estiver ocupada. Os modelos permitidos e limites podem ser ajustados somente
na configuração do serviço, não pelo cliente.
