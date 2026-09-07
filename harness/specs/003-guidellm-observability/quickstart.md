# Quickstart: benchmark GuideLLM do OVMS

A partir de `app`, mantenha `api` e `ovms` ativos e saudáveis:

```powershell
docker compose up -d api ovms
```

No PowerShell, a partir de `harness`:

```powershell
.\scripts\Invoke-GuideLLMBenchmark.ps1 -Model qwen3-8b -PromptTokens 32 -OutputTokens 32 -Concurrency 1 -MaxRequests 1
```

O script usa a rede interna do Compose e grava a saída em:

`harness/.agent-work/benchmarks/guidellm/<run-id>/`

Ele faz um preflight em `/v1/models` porque o GuideLLM `0.7.3` usa `/health`
na validação padrão e o OVMS local responde `400` nesse caminho. O preflight
não gera texto; a medição usa `/v1/chat/completions` com streaming.

Arquivos principais:

- `benchmarks.json`: configuração, amostras e estatísticas completas.
- `benchmarks.csv`: resumo tabular por benchmark/requisição.
- `benchmarks.html`: relatório visual autocontido.
- `run-manifest.json`: modelo, limites, image digest, endpoint, tokenizer e código de saída.

Para o Qwen3 1.7B:

```powershell
.\scripts\Invoke-GuideLLMBenchmark.ps1 -Model qwen3-1.7b -PromptTokens 32 -OutputTokens 24 -Concurrency 1 -MaxRequests 1
```

Para uma pequena concorrência controlada:

```powershell
.\scripts\Invoke-GuideLLMBenchmark.ps1 -Model qwen3-8b -PromptTokens 32 -OutputTokens 24 -Concurrency 2 -MaxRequests 4
```

`Concurrency 1` usa o perfil síncrono; valores maiores usam o perfil concorrente. O primeiro teste é deliberadamente pequeno. Não compare execuções com modelos, limites, temperatura, estado de aquecimento ou recursos diferentes.

## Como abrir e consultar o resultado

O script imprime o caminho absoluto no formato `GUIDELLM_RUN=...`. Para abrir o
relatório visual da execução, substitua `<run-id>` pelo valor impresso:

```powershell
Invoke-Item .\.agent-work\benchmarks\guidellm\<run-id>\benchmarks.html
```

Para listar as execuções e inspecionar os dados tabulares:

```powershell
Get-ChildItem .\.agent-work\benchmarks\guidellm -Directory
Import-Csv .\.agent-work\benchmarks\guidellm\<run-id>\benchmarks.csv |
  Format-List
Get-Content .\.agent-work\benchmarks\guidellm\<run-id>\run-manifest.json
```

`run.log` contém a saída operacional do comando. Uma execução só é marcada
como concluída pelo runner quando os três relatórios existem e há pelo menos
uma requisição bem-sucedida; um relatório com apenas erros não é uma medição
válida.

## Interpretação

- `output_tokens_per_second`: velocidade de geração; não é o mesmo que throughput agregado.
- Throughput agregado representa tokens de saída de todas as requisições divididos pelo tempo da janela do benchmark.
- Em uma execução síncrona de uma única amostra, o resumo agregado do GuideLLM
  0.7.3 pode mostrar `0.0`; use `output_tokens_per_second` da requisição no
  `benchmarks.json` e repita com mais requisições para uma leitura agregada.
- TTFT é o tempo até o primeiro conteúdo; ITL/TPOT mede o intervalo entre conteúdos sucessivos.
- Latência e percentis representam a experiência das requisições, incluindo fila e rede.
- A origem das contagens deve ser conferida no manifesto e no JSON: uso retornado pelo OVMS quando presente ou tokenizer local usado pelo GuideLLM.
- Pacotes/eventos SSE não equivalem a tokens.
- O GuideLLM não prova a GPU. Para isso, confira `docker logs app-ovms-1` e os graphs com `device: "GPU"`.
