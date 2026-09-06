# Quickstart: OpenVINO Model Server API

Os comandos de aplicação abaixo são executados em PowerShell a partir de
`C:\Users\mdbaa\development\Agents\server-agents\app`. Os comandos de
diagnóstico/relatórios do harness usam o runner a partir de
`C:\Users\mdbaa\development\Agents\server-agents\harness`.

## Prerequisites

- Docker Desktop usando contexto Linux e uma configuração WSL2/GPU Intel
  comprovada pelo relatório de runtime; no Windows a configuração documentada
  usa `/dev/dxg` e `/usr/lib/wsl`.
- A imagem versionada `openvino/model_server:2026.3.1-gpu` e seu digest
  verificados antes do primeiro pull.
- Modelo `OpenVINO/Qwen3-1.7B-int4-ov`, revisão registrada e artefatos íntegros
  em `app/models/`. O preparo é persistente e não faz parte do build da API.

## First preparation

1. Copie `.env.example` para `.env` e revise limites e modelo; não coloque
   tokens ou segredos no arquivo versionado.
2. Execute o procedimento de preparo do modelo documentado pelo agente
   OpenVINO e confirme a origem/revisão/precisão antes de iniciar OVMS.
3. Confirme o acesso GPU no daemon/container; não troque `/dev/dxg` por
   `/dev/dri` sem evidência de Linux nativo.

## Start and validate

Em `app/`, depois das pré-condições:

```powershell
docker compose up -d --build
curl.exe http://127.0.0.1:8000/healthz
curl.exe http://127.0.0.1:8000/readyz
Start-Process http://127.0.0.1:8000/docs
```

A API publica somente `127.0.0.1:8000`. O OVMS não publica porta no host; ele
é acessado pela API na rede Compose.

## Requests

```powershell
$body = '{"text":"Explique em português o que é OpenVINO em poucas palavras.","max_tokens":64,"temperature":0.2}'
curl.exe -X POST http://127.0.0.1:8000/v1/generate/sync -H "Content-Type: application/json" -d $body
curl.exe -X POST http://127.0.0.1:8000/v1/generate/async -H "Content-Type: application/json" -d $body
curl.exe -N -X POST http://127.0.0.1:8000/v1/generate/stream -H "Accept: text/event-stream" -H "Content-Type: application/json" -d $body
```

Linux:

```bash
curl -X POST http://127.0.0.1:8000/v1/generate/sync -H 'Content-Type: application/json' -d '{"text":"Explique em português o que é OpenVINO.","max_tokens":64}'
curl -X POST http://127.0.0.1:8000/v1/generate/async -H 'Content-Type: application/json' -d '{"text":"Explique em português o que é OpenVINO.","max_tokens":64}'
curl -N -X POST http://127.0.0.1:8000/v1/generate/stream -H 'Accept: text/event-stream' -H 'Content-Type: application/json' -d '{"text":"Explique em português o que é OpenVINO.","max_tokens":64}'
```

`sync` e `async` aguardam o resultado na mesma requisição. `async` permite
concorrência de I/O, mas não acelera individualmente a geração. Um delta SSE
pode ser parte de palavra, várias palavras ou vazio, conforme o upstream.

## Evidence and limits

Testes pytest e contrato rodam sem GPU/modelo. A aceitação real exige evidência
separada de imagem, modelo carregado, `GPU` explícito no OVMS, resposta das três
rotas, stream incremental, cancelamento e medições de TTFT/latência/tokens/s.
Se a pré-condição Windows/WSL2 não existir, a entrega fica parcialmente pronta
e o relatório deve apontar a correção concreta, sem fallback silencioso para CPU.
