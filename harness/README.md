# Server-agents harness

This directory is the canonical Codex harness for the sibling application.
It contains the orchestrator instructions, native Codex subagents, Spec Kit
artifacts, installed-skill map, runner and safe cleanup command.

## Start Codex

From any PowerShell location, start in the harness and pass the application as
an explicit writable target:

~~~powershell
codex --cd C:\Users\mdbaa\development\Agents\server-agents\harness --add-dir C:\Users\mdbaa\development\Agents\server-agents\app
~~~

The command was validated against Codex CLI 0.153.4. The project configuration
keeps the existing model and reasoning policy and limits this harness to two
active subagents.

## Feature, Spec Kit and PR flow

Before a new feature, the principal reports the current branch and asks for
explicit confirmation. After confirmation, from the harness directory run:

~~~powershell
.\scripts\New-FeatureBranch.ps1 -Name "configure github flow" -Confirmed
~~~

The command fetches `origin/develop` and creates `feature/configure-github-flow`
from that base. It refuses a dirty checkout and never stashes or discards
changes. If the feature branch already exists, inspect it first and pass
`-ReuseExisting` only when reuse is intentional. The Spec Kit script is then
run explicitly; it creates the numbered spec directory and feature metadata but
does not create or switch a branch:

~~~powershell
.\.specify\scripts\powershell\create-new-feature.ps1 -ShortName "github-flow" "Configure Spec Kit and pull request flow"
~~~

Before publishing, the principal reviews and commits only the relevant diff,
then asks:

~~~text
Posso fazer o push da branch <branch> para o repositório michaeldouglas/openvino-models-server e abrir ou atualizar o PR para develop?
~~~

No push or PR publication occurs without that confirmation. The principal
coordinates publication; subagents never publish independently.

The root workflows are:

- `ensure-feature-pr.yml`: idempotent `feature/**` to `develop` PR creation;
- `promote-develop-to-main.yml`: idempotent `develop` to `main` PR after an
  actual merge into `develop`;
- `pr-branch-policy.yml`: same-repository source/target validation;
- `harness-validation.yml`: lightweight harness validation (`validate-harness`).

They require the repository's Actions setting to allow the workflow token to
create PRs. Local MCP authentication is separate. Rulesets report `main` and
`develop` as protected, but the installed MCP cannot expose their full
administrative configuration or required-check state.

## Graphify

The harness graph is at `graphify-out/graph.json` and was initialized with
local AST extraction plus deterministic communities. Use `graphify query
"<question>"`, `graphify path "<A>" "<B>"` or `graphify explain "<concept>"`
from this directory before broad source searches. The application has no graph
until it contains implementation code; then run
`graphify update C:\Users\mdbaa\development\Agents\server-agents\app` from
the orchestrator and keep that output in the app's canonical `graphify-out/`.

The repository's post-commit and post-checkout Graphify hooks are installed;
their rebuild log is routed to `harness/.agent-work/cache/graphify/`. Reinstalling
the hooks may restore the tool default, so check the route if the hooks are
recreated.

## Run a command with isolated outputs

The runner derives paths from its own location and creates a unique run
directory. Arguments are passed as individual array elements:

~~~powershell
.\scripts\Invoke-AgentCommand.ps1 -Agent api-engineer -FilePath python -ArgumentList @("--version") -WorkingDirectory C:\Users\mdbaa\development\Agents\server-agents\app
~~~

Use the returned run directory for logs, reports, temporary files and scratch
work. A failed child command keeps its exit code.

## Preview and apply cleanup

Cleanup previews by default and only touches completed or failed runs:

~~~powershell
.\scripts\Clean-AgentWork.ps1
.\scripts\Clean-AgentWork.ps1 -RunId <run-id>
~~~

Apply cleanup only after reviewing the preview:

~~~powershell
.\scripts\Clean-AgentWork.ps1 -Apply -RunId <run-id>
.\scripts\Clean-AgentWork.ps1 -Apply -Caches
~~~

The cleanup command refuses targets outside .agent-work, reparse points, active
runs, models, source code, tests, specs and Graphify output.

## GuideLLM benchmark

O app possui um serviço Compose opcional `guidellm`, fixado na imagem publicada
`v0.7.3` por digest. Ele mede diretamente o OVMS pela rede interna; não mede o
overhead das rotas FastAPI e não deve ser iniciado pelo `docker compose up`
normal. Com `api` e `ovms` saudáveis, execute a partir deste diretório:

~~~powershell
.\scripts\Invoke-GuideLLMBenchmark.ps1 -Model qwen3-8b -PromptTokens 32 -OutputTokens 32 -Concurrency 1 -MaxRequests 1
~~~

Os relatórios ficam em
`.agent-work/benchmarks/guidellm/<run-id>/`: `benchmarks.json`,
`benchmarks.csv`, `benchmarks.html` e `run-manifest.json`. O quickstart da
feature em `specs/003-guidellm-observability/quickstart.md` explica como trocar
modelo, entrada, saída, concorrência e limites, além de interpretar tokens/s,
TTFT, ITL, latência e percentis. Pesos não são copiados; os tokenizers são
montados somente para leitura a partir de `app/models`. O script imprime
`GUIDELLM_RUN=...`; abra `benchmarks.html` com `Invoke-Item` nesse diretório e
consulte `benchmarks.csv`, `benchmarks.json`, `run-manifest.json` e `run.log`
para os dados detalhados. Uma execução só passa quando há requisições
bem-sucedidas, evitando tratar um relatório de erros como desempenho medido.
