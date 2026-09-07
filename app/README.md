# Local LLM workspace

Este diretório contém o produto local, separado por responsabilidade:

```text
app/
├── services/api/                  pacote instalável e API HTTP
├── services/benchmark/            executor isolado e resultados locais
├── deploy/                        Compose e configuração de implantação
├── models/                        pesos, manifests e cache local (ignorado)
└── scripts/                       preparação idempotente de modelos
```

## API e framework

O serviço em `services/api` publica o pacote `local-llm` e o comando `local-llm`.
Ele mantém a fronteira do provedor separada da API, usa OVMS como adaptador
local e expõe tanto as rotas legadas `/v1/generate/*` quanto o contrato
OpenAI-compatível `/v1/chat/completions`.

```powershell
python -m pip install -e .\services\api
local-llm models list
local-llm serve --host 127.0.0.1 --port 8000
```

Para integrar com LangChain, instale o extra opcional e aponte um cliente
OpenAI para `http://127.0.0.1:8000/v1`. O runtime local não encaminha chamadas
para provedores pagos automaticamente; OpenAI e outros provedores continuam
sendo selecionados explicitamente pela aplicação consumidora.

## Execução com Docker

```powershell
Copy-Item .\deploy\.env.example .\.env
.\scripts\prepare-models.ps1
docker compose --project-directory .\deploy -f .\deploy\compose.yaml up -d --build
```

O serviço OVMS monta `models/`, enquanto os resultados do benchmark ficam em
`services/benchmark/results/`. Pesos, cache e resultados são dados locais e não
fazem parte do pacote nem do Git.

Consulte [services/api/README.md](services/api/README.md) para o contrato HTTP,
configuração detalhada e validação.
