# openvino-models-server

API FastAPI para enviar texto a um LLM servido pelo OpenVINO Model Server
(OVMS). A aplicação é deliberadamente dividida em dois processos:

```text
cliente -> api (FastAPI, localhost:8000) -> ovms (rede Compose, GPU Intel)
                                      \-> models/ (volume persistente)
```

O FastAPI não importa OpenVINO, não carrega pesos e não mantém histórico. O
OVMS é o único responsável por carregar o modelo e executar a geração.

## Estrutura

- `src/openvino_models_server/api`: schemas, rotas e contrato HTTP.
- `src/openvino_models_server/application`: caso de uso e protocolo de
  inferência, sem detalhes do OVMS.
- `src/openvino_models_server/infrastructure`: adaptador HTTP sync/async e
  parser SSE do OVMS.
- `tests`: testes permanentes com upstream controlado; não exigem GPU/modelo.
- `models`: armazenamento persistente local, ignorado pelo Git.
- `compose.yaml`: serviços `api` e `ovms`.

## Modelo e GPU

O candidato inicial é `OpenVINO/Qwen3-1.7B-int4-ov`, revisão `main`, IR INT4
assimétrica e licença Apache-2.0. Alternativas registradas no Spec Kit são
`OpenVINO/Qwen2.5-1.5B-Instruct-int4-ov` e `OpenVINO/Qwen3-4B-int4-ov`.
Nenhuma destas escolhas substitui teste de qualidade em português, consumo de
memória ou desempenho na GPU real.

O Compose usa `openvino/model_server:2026.3.1-gpu` e `--target_device GPU`.
Essa é uma imagem versionada, mas o digest deve ser conferido e fixado quando
o daemon local fizer a inspeção do manifesto. Em Windows, só use a configuração
`/dev/dxg` e `/usr/lib/wsl` se WSL2 e o Docker Desktop realmente expuserem esses
recursos. Linux nativo usa uma configuração distinta com `/dev/dri`; não copie
os argumentos entre os ambientes.

O diagnóstico atual confirmou o Intel Core Ultra 7 258V, Windows 11 e GPU Intel
Arc 140V no host, mas ainda não confirmou OpenVINO no host, WSL2, visibilidade
da GPU no container ou geração real. Portanto, não há fallback automático para
CPU.

## Configuração e inicialização

No PowerShell, a partir desta pasta:

```powershell
Copy-Item .env.example .env
# Revise .env e confirme as pré-condições de GPU/modelo.
docker context use desktop-linux
docker compose config
docker compose up -d --build
```

Os pesos serão persistidos em `app/models/` e não entram na imagem da API.
Preparação/download deve ser executado separadamente e de forma idempotente,
conforme o relatório do agente OpenVINO. O serviço OVMS não publica porta no
host; somente a API fica em `127.0.0.1:8000`.

Operacional:

```powershell
curl.exe http://127.0.0.1:8000/healthz
curl.exe http://127.0.0.1:8000/readyz
Start-Process http://127.0.0.1:8000/docs
```

`/healthz` verifica apenas o processo FastAPI. `/readyz` consulta a capacidade
do OVMS/modelo sem gerar texto. `/docs` e `/openapi.json` são fornecidos pelo
FastAPI.

## Rotas de geração

As três rotas aceitam o mesmo corpo:

```json
{"text":"Explique em português o que é OpenVINO em poucas palavras.","max_tokens":64,"temperature":0.2}
```

`max_tokens` padrão 128 (máximo configurado 512), `temperature` padrão 0,2
(0–2) e texto de entrada limitado por padrão a 12.000 caracteres. O cliente não
escolhe modelo, URL ou caminho local.

```powershell
curl.exe -X POST http://127.0.0.1:8000/v1/generate/sync -H "Content-Type: application/json" -d '{"text":"Explique em português o que é OpenVINO.","max_tokens":64}'
curl.exe -X POST http://127.0.0.1:8000/v1/generate/async -H "Content-Type: application/json" -d '{"text":"Explique em português o que é OpenVINO.","max_tokens":64}'
curl.exe -N -X POST http://127.0.0.1:8000/v1/generate/stream -H "Accept: text/event-stream" -H "Content-Type: application/json" -d '{"text":"Explique em português o que é OpenVINO.","max_tokens":64}'
```

No Linux, use os mesmos URLs com `curl` e aspas simples. A rota sync executa
I/O bloqueante no threadpool do FastAPI; a async usa `httpx.AsyncClient` e
`async/await`; ambas aguardam o resultado na mesma requisição. Streaming
encaminha eventos `delta`, `done` e `error` reais. Um delta pode ser parte de
uma palavra, várias palavras ou vazio; concatene os textos dos deltas.

Erros retornam `{ "error": { "code", "message", "request_id" } }` com códigos
para entrada inválida, capacidade, upstream indisponível/falho e timeout.
Prompts e respostas completas não são registrados por padrão.

## Testes e evidências

```powershell
python -m pytest
python -m ruff check src tests
python -m mypy src
```

Os testes controlados não comprovam GPU nem modelo real. A aceitação da stack
exige registrar imagem/digest, modelo/revisão/precisão, logs de carregamento,
dispositivo GPU explícito, as três respostas reais, streaming incremental,
cancelamento e medições de startup, primeira chamada, aquecimento, TTFT,
latência, tokens/s e concorrência controlada.
