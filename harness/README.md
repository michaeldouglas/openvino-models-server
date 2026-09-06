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

The future API belongs in the sibling app. This preparation does not implement
endpoints, install OpenVINO, download models, run inference, benchmark models or
start Docker.
