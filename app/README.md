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
- `scripts/prepare-models.ps1`: prepara os dois artefatos Qwen e gera a configuração multi-modelo do OVMS.
- `compose.yaml`: serviços `api` e `ovms`.

## Modelo e GPU

Os modelos configurados são `OpenVINO/Qwen3-1.7B-int4-ov` (alias
`qwen3-1.7b`) e `OpenVINO/Qwen3-8B-int4-ov` (alias `qwen3-8b`), ambos em
INT4 e com licença Apache-2.0. O 1.7B permanece como padrão e fallback. O
artefato 8B tem aproximadamente 4,88 GB e requer validação de memória e
desempenho na GPU real; qualidade em português não é inferida do tamanho.

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
Prepare os modelos antes do boot, de forma idempotente:

```powershell
.\scripts\prepare-models.ps1
```

O script reutiliza artefatos completos, prepara somente o que estiver faltando
e gera `app/models/config.json`. Use `-SkipDownload` para somente registrar os
modelos já disponíveis. O serviço OVMS usa esse `config.json` para servir
múltiplos graphs; não baixa modelos durante o boot e não publica porta no host.
Somente a API fica em `127.0.0.1:8000`.

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
(0–2) e texto de entrada limitado por padrão a 12.000 caracteres. O cliente
pode escolher somente `qwen3-1.7b` ou `qwen3-8b`; URL e caminho local nunca são
aceitos.

```powershell
curl.exe -X POST http://127.0.0.1:8000/v1/generate/sync -H "Content-Type: application/json" -d '{"text":"Explique em português o que é OpenVINO.","max_tokens":64}'
curl.exe -X POST http://127.0.0.1:8000/v1/generate/sync -H "Content-Type: application/json" -d '{"model":"qwen3-8b","text":"Explique em português o que é OpenVINO.","max_tokens":64}'
curl.exe -X POST http://127.0.0.1:8000/v1/generate/async -H "Content-Type: application/json" -d '{"text":"Explique em português o que é OpenVINO.","max_tokens":64}'
curl.exe -N -X POST http://127.0.0.1:8000/v1/generate/stream -H "Accept: text/event-stream" -H "Content-Type: application/json" -d '{"text":"Explique em português o que é OpenVINO.","max_tokens":64}'
```

No Linux, use os mesmos URLs com `curl` e aspas simples. A rota sync executa
I/O bloqueante no threadpool do FastAPI; a async usa `httpx.AsyncClient` e
`async/await`; ambas aguardam o resultado na mesma requisição. Streaming
encaminha eventos `delta`, `done` e `error` reais. Um delta pode ser parte de
uma palavra, várias palavras ou vazio; concatene os textos dos deltas.

`GET /v1/models` informa quais aliases estão prontos e qual é o padrão. A
seleção é por requisição, portanto não há troca global que possa afetar uma
geração concorrente. Se o 8B não estiver pronto, o 1.7B continua disponível.

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
