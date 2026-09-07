# Tasks: Observabilidade de desempenho com GuideLLM

## Phase 1: Setup

- [x] T001 Atualizar `app/compose.yaml` com o serviço opcional `guidellm`, image digestada, rede e mounts read-only de tokenizer.
- [x] T002 Criar `harness/scripts/Invoke-GuideLLMBenchmark.ps1` com caminhos derivados do script, parâmetros validados, manifesto e propagação de falhas.
- [x] T003 Registrar a decisão de versão, endpoint, modelo e origem da tokenização em `harness/specs/003-guidellm-observability/research.md`.

## Phase 2: Documentation

- [x] T004 Documentar execução, parâmetros, relatórios e interpretação em `harness/specs/003-guidellm-observability/quickstart.md` e README do harness.
- [x] T005 Conferir o mapa/registro do harness; o runner é referenciado pelo README e a matriz de skills permanece sem duplicação.

## Phase 3: Validation

- [x] T006 Validar `docker compose config -q` e `guidellm --version` no container digestado.
- [x] T007 Executar benchmark curto real com concorrência 1 contra OVMS, se os serviços estiverem prontos.
- [x] T008 Conferir JSON/CSV/HTML, tokens por segundo, TTFT, latência, percentis, falhas e origem da contagem.
- [x] T009 Conferir evidência independente de GPU nos logs/configuração do OVMS.
- [x] T010 Atualizar Graphify no escopo do app e registrar o resultado no `.agent-work`.

## Completion criteria

- Nenhuma rota ou dependência de produção do FastAPI é alterada.
- Falhas do benchmark retornam código não zero.
- Relatórios descartáveis não aparecem na raiz do app/harness nem entram no Git.
- A execução real é distinguida da validação sintática e da evidência de GPU.
