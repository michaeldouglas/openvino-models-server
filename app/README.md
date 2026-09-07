# Local LLM workspace

Este diretório contém o produto local, separado por responsabilidade:

```text
app/
├── packages/local-llm/            pacote instalável e API HTTP
├── packages/benchmark-runner/     executor e resultados locais
├── runtime/                       deployment, modelos e scripts
└── examples/                      integrações externas
```

## API e framework

O pacote em `packages/local-llm` publica o pacote `local-llm` e o comando `local-llm`.
Ele mantém a fronteira do provedor separada da API, usa OVMS como adaptador
local e expõe tanto as rotas legadas `/v1/generate/*` quanto o contrato
OpenAI-compatível `/v1/chat/completions`.

```powershell
python -m pip install -e .\packages\local-llm
local-llm models list
local-llm serve --host 127.0.0.1 --port 8000
```

Para integrar com LangChain, instale o extra opcional e aponte um cliente
OpenAI para `http://127.0.0.1:8000/v1`. O runtime local não encaminha chamadas
para provedores pagos automaticamente; OpenAI e outros provedores continuam
sendo selecionados explicitamente pela aplicação consumidora.

## Execução com Docker

```powershell
Copy-Item .\runtime\deployment\.env.example .\.env
.\runtime\scripts\prepare-models.ps1
docker compose --project-directory .\runtime\deployment -f .\runtime\deployment\compose.yaml up -d --build
```

Para priorizar latência e carregar somente o Qwen3 1.7B, use o perfil rápido:

```powershell
docker compose --project-directory .\runtime\deployment `
  -f .\runtime\deployment\compose.yaml `
  -f .\runtime\deployment\compose.fast.yaml up -d --build
```

O perfil completo continua carregando os modelos configurados em
`runtime/models/config.json`. No perfil rápido, `FAST_MAX_CONCURRENCY` controla
quantas gerações a API aceita simultaneamente; compare 1, 2 e 4 no hardware
real antes de escolher o valor padrão.

O serviço OVMS monta `runtime/models/`, enquanto os resultados do benchmark ficam em
`packages/benchmark-runner/results/`. Pesos, cache e resultados são dados locais e não
fazem parte do pacote nem do Git.

Consulte [packages/local-llm/README.md](packages/local-llm/README.md) para o contrato HTTP,
configuração detalhada e validação.
