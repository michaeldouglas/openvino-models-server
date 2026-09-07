# Research: GuideLLM com OVMS

## Decisões

- Fixar GuideLLM em `v0.7.3`, release publicada em 31/07/2026, com imagem digestada `ghcr.io/vllm-project/guidellm@sha256:e3ad2371bfa8e42f2c3d1251b62d0d9c9706c27ae2143c8c048eb5fc6aebb558`.
- Usar `openai_http` com `target=http://ovms:8000`, `model=qwen3-8b`, `request_format=/v1/chat/completions` e `stream=true`.
- A versão `0.7.3` valida por padrão `target/health`, que retorna `400` no OVMS usado. O runner desativa somente essa validação interna (`validate_backend=false`) e faz preflight explícito em `http://ovms:8000/v1/models` antes da medição.
- Montar os diretórios existentes de modelos somente leitura para que o GuideLLM reutilize o tokenizer sem copiar pesos.
- Usar dados sintéticos com limites pequenos na primeira execução; a contagem de tokens de entrada/saída deve vir do uso retornado pelo endpoint ou do tokenizer explicitamente montado.
- Exportar `json`, `csv` e `html` em uma execução com identificador único.
- Usar `sample_size` igual a `MaxRequests`: no GuideLLM 0.7.3, `sample_size=0`
  remove as amostras completas e deixa os agregados de tokens/s sem dados úteis.
- O GuideLLM 0.7.3 inclui `continuous_usage_stats` por padrão no streaming,
  mas o OVMS escolhido aceita apenas `include_usage`; o runner remove esse
  campo incompatível durante a normalização do corpo.

## Fontes oficiais consultadas

- GuideLLM README: instalação, container, backend OpenAI, perfis e saídas: <https://github.com/vllm-project/guidellm>
- Release v0.7.3 e digest: <https://github.com/vllm-project/guidellm/releases/tag/v0.7.3>
- Backend OpenAI HTTP: <https://github.com/vllm-project/guidellm/blob/main/docs/guides/backends.md>
- Métricas: <https://github.com/vllm-project/guidellm/blob/main/docs/guides/metrics.md>
- Saídas: <https://github.com/vllm-project/guidellm/blob/main/docs/guides/outputs.md>

## Limitações

GuideLLM mede o caminho até o endpoint e calcula métricas do cliente. A confirmação de GPU continua baseada nos logs/configuração do OVMS e no grafo com `device: "GPU"`; tokens enviados em pacotes SSE não são contados como tokens. Uma execução curta não representa capacidade de produção.

## Validação local

Em `qwen3-8b-smoke6`, com `Concurrency=1`, `MaxRequests=1`, 16 tokens de
entrada solicitados e 4 de saída, houve 1 requisição bem-sucedida e 0 erros.
O tokenizer/template de chat resultou em 16 tokens de entrada nessa execução,
4 tokens de saída, latência de aproximadamente 274 ms, TTFT de aproximadamente
274 ms e `output_tokens_per_second` por requisição de aproximadamente 14,6.
Os percentis de uma única amostra coincidem com a própria amostra; isso não é
um benchmark de capacidade. O resumo de throughput agregado do console pode
mostrar zero nessa configuração curta, portanto a documentação orienta
consultar também a métrica por requisição no JSON.
