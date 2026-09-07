# Quickstart: Validate the Fast Performance Profile

From the repository root, use the application deployment directory:

```powershell
cd app
docker compose --project-directory .\runtime\deployment `
  -f .\runtime\deployment\compose.yaml `
  -f .\runtime\deployment\compose.fast.yaml up -d --build
```

Confirm readiness:

```powershell
curl.exe http://127.0.0.1:8000/readyz
curl.exe http://127.0.0.1:8000/v1/models
```

Run a short warm generation:

```powershell
curl.exe -X POST http://127.0.0.1:8000/v1/generate/stream `
  -H "Content-Type: application/json" `
  -d '{"model":"qwen3-1.7b","text":"Responda em uma frase: por que medir latência?","max_tokens":32,"temperature":0.2}'
```

Run the controlled benchmark after the stack is ready. Record cold start
separately from warm iterations, and compare concurrency 1, 2, and 4 without
changing prompt, output limit, device, or model between runs.

Expected result: the fast profile reports only the enabled fast model as ready,
returns a valid response, and produces timing metadata without exposing the full
prompt or response in operational logs.
