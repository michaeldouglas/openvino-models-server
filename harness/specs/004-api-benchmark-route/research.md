# Research: benchmark iniciado pela API

## Decisões

- Reutilizar o GuideLLM `v0.7.3` e o digest já validado na feature
  `003-guidellm-observability`, evitando instalar a ferramenta nas dependências
  do FastAPI.
- Criar um serviço `benchmark-runner` interno no Compose, com uma API mínima
  para iniciar/status/relatório e subprocesso assíncrono para o GuideLLM.
- Gravar resultados em `/results/<run-id>` dentro do executor, montado em
  `app/results/` no host. O root `.gitignore` e o `.dockerignore` da API
  excluem essa saída.
- Manter o benchmark direto no OVMS. A rota não altera as três rotas públicas
  de geração nem mede automaticamente o overhead do FastAPI.
- Rejeitar uma nova execução quando o limite ativo for atingido. Não haverá
  fila ilimitada, Redis, Celery ou banco nesta primeira versão.
- Expor somente `json`, `csv` e `html` por identificador. O executor nunca
  aceita caminho, comando, URL ou argumento livre do cliente.

## Evidência e referências

- A documentação oficial do GuideLLM descreve o backend HTTP OpenAI, perfis,
  streaming e opções de saída: <https://github.com/vllm-project/guidellm>.
- As métricas de requisições, tokens, TTFT, latência e percentis estão em:
  <https://github.com/vllm-project/guidellm/blob/main/docs/guides/metrics.md>.
- A imagem e a versão foram verificadas na execução anterior e permanecem
  fixadas no Compose e no Dockerfile do executor.

## Alternativas descartadas

- **Montar `/var/run/docker.sock` no FastAPI**: daria controle amplo do daemon e
  quebraria o princípio de menor privilégio.
- **Importar GuideLLM dentro da API**: misturaria ferramenta operacional com
  dependências de produção e poderia bloquear o processo da API.
- **Executar tudo com `BackgroundTasks` do FastAPI**: não oferece isolamento
  suficiente nem controle claro sobre processos longos após reinício.
