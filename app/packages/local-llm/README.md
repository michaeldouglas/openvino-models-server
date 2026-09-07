# `local-llm` API

Pacote instalável para servir modelos locais por meio do OpenVINO Model Server
(OVMS). A API não carrega pesos nem importa o runtime do OpenVINO: ela valida
requisições, seleciona um alias de modelo e delega a geração ao OVMS.

## Desenvolvimento

A partir de `app/`:

```powershell
python -m pip install -e .\packages\local-llm
python -m pytest .\packages\local-llm\tests
python -m ruff check .\packages\local-llm\src .\packages\local-llm\tests
python -m mypy .\packages\local-llm\src
```

O pacote fornece o comando:

```powershell
local-llm models list
local-llm models info qwen3-1.7b
local-llm serve --host 127.0.0.1 --port 8000 --model qwen3-1.7b
```

O extra `local-llm[langchain]` instala `langchain-openai` para o adaptador
OpenAI-compatível. LangChain pode usar o endpoint local com `base_url` sem que
este projeto passe a depender de LangChain no caminho principal.

## Configuração e performance

As variáveis são lidas de `.env` no diretório de trabalho. O padrão é o modelo
`qwen3-1.7b`, com `DEFAULT_MAX_TOKENS=128`, `MAX_TOKENS_LIMIT=512` e
`MAX_CONCURRENCY=2`. Para respostas interativas rápidas, use `max_tokens` de
32–64 e streaming; limites maiores aumentam diretamente o tempo de geração.

O OVMS é responsável pelo cache de modelo e pelo scheduler. O Compose monta
`runtime/models/.ov_cache` em `/opt/cache` e desativa o polling de configuração durante
a execução. Não altere o modelo 1.7B para testar o 8B: variantes experimentais
devem usar outro diretório e outro alias.

## Contrato HTTP

Operacional:

```text
GET /healthz    processo HTTP vivo
GET /readyz     OVMS/modelos acessíveis
GET /v1/models  aliases configurados e status
```

Geração legada:

```json
{"text":"Explique OpenVINO em uma frase.","max_tokens":64,"temperature":0.2}
```

```text
POST /v1/generate/sync
POST /v1/generate/async
POST /v1/generate/stream
```

Contrato OpenAI-compatível:

```json
{
  "model": "qwen3-1.7b",
  "messages": [{"role": "user", "content": "Explique OpenVINO."}],
  "max_tokens": 64,
  "stream": true
}
```

```text
POST /v1/chat/completions
```

O streaming retorna `text/event-stream`, com chunks compatíveis com o formato
de chat e o terminador `data: [DONE]`. Apenas aliases configurados são aceitos;
URL, caminho local e provedor remoto nunca são recebidos pelo cliente.

## Modelos e implantação

Prepare os modelos a partir de `app/` com:

```powershell
.\runtime\scripts\prepare-models.ps1
docker compose --project-directory .\runtime\deployment -f .\runtime\deployment\compose.yaml up -d --build
```

O 1.7B é o perfil rápido padrão. O 8B é opcional e deve ser medido na GPU
real. Para preparar uma variante experimental de scheduler, use parâmetros
explícitos, por exemplo `.\scripts\prepare-models.ps1 -Qwen8BMaxNumSeqs 2`.
Artefatos completos existentes são sempre reutilizados; o script não os
sobrescreve automaticamente. O manifesto do modelo, os pesos e o cache ficam
fora do pacote Python.

## Benchmarks

O executor fica em `packages/benchmark-runner`, com imagem, dependências, testes e
resultados próprios. Para habilitar o gateway de benchmark pela API:

```powershell
docker compose --project-directory .\runtime\deployment -f .\runtime\deployment\compose.yaml `
  --profile benchmark-api up -d --build
```

Os resultados são gravados em `packages/benchmark-runner/results/<run-id>/` e não são
misturados ao código da API. O benchmark mede o caminho OVMS selecionado; as
medições devem registrar modelo, dispositivo, aquecimento, TTFT, latência,
tokens/s e concorrência.
