## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Canonical harness orchestration

This file is the canonical project instruction set for the orchestrator session.
The primary agent is the orchestrator; do not create or require another
orchestrator subagent.

### Resolved workspaces

- Harness: C:\Users\mdbaa\development\Agents\server-agents\harness
- Application target: C:\Users\mdbaa\development\Agents\server-agents\app
- Agent work area: C:\Users\mdbaa\development\Agents\server-agents\harness\.agent-work
- Shared Git root: C:\Users\mdbaa\development\Agents\server-agents

Start Codex in the harness and make the sibling application explicit:

    codex --cd C:\Users\mdbaa\development\Agents\server-agents\harness --add-dir C:\Users\mdbaa\development\Agents\server-agents\app

This command is supported by Codex CLI 0.153.4. The harness remains the
instruction root; --add-dir grants the app as an explicit additional target.
Do not change model, reasoning effort, approval policy, sandbox policy, or global
environment settings unless the user explicitly requests it.

### Orchestrator responsibilities

The orchestrator MUST:

- Drive the Spec Kit sequence: specification, plan, tasks, acceptance criteria,
  and implementation only when the user authorizes implementation.
- Use Graphify before codebase investigation when the target has
  graphify-out/graph.json; use focused query, path, or explain calls. The harness
  now has a raw AST graph at graphify-out/graph.json; the app does not have a graph
  because it has no implementation to index. Do not simulate app Graphify results;
  establish an app graph only after the app has code.
- Read the complete SKILL.md for every skill selected for a task and respect each
  skill's confirmation and evidence boundaries.
- Define the API/inference contract before delegating dependent implementation.
- Delegate only bounded work to the four configured agents below. Start with at
  most two active subagents, even though the Codex configuration can support more
  in other projects.
- Coordinate shared files serially. One agent owns a file at a time; dependency
  manifests, lockfiles, common configuration, and Graphify outputs are serialized.
- Review each returned summary, verify evidence, and integrate only after checking
  paths, exit codes, and acceptance criteria.
- Apply the temporary-file, safe-cleanup, and model-artifact rules in this file to
  every subagent.

Each delegation MUST include: objective, Spec Kit task when applicable, absolute
harness and app paths, working directory, permitted files, relevant skills,
dependencies, completion criteria, and the exclusive
.agent-work/runs/<run-id>/<agent>/ output directory. Agents MUST return changed
files, commands and exit codes, evidence paths, results, and pending items.
Subagents MUST NOT spawn further subagents or create worktrees automatically.

### Agent routing

- openvino-engineer: hardware and runtime evidence, model compatibility and
  preparation, generation, optimization, and measurement. Uses the installed
  Intel OpenVINO skills listed in docs/skills-map.md. Plan first and require
  explicit confirmation before mutation, downloads, installation, inference,
  container start, artifact generation, or benchmarks.
- api-engineer: HTTP contracts, typed schemas, lifecycle, inference boundary,
  concurrency, errors, and API tests. Uses fastapi-templates,
  python-type-safety, and python-testing-patterns.
- platform-engineer: Docker, configuration, device access, model persistence,
  health checks, and CI. Uses docker; the requested github-actions-templates
  skill is not installed and MUST be reported before any CI work. Uses the
  OpenVINO Model Server skill only when OVMS is selected.
- quality-reviewer: independent findings-first review of behavior, security,
  tests, lint, typing, and evidence. Uses code-review-excellence,
  ruff-recursive-fix, python-testing-patterns, and python-type-safety. It may
  write temporary test outputs under its exclusive work directory, but MUST NOT
  edit application code unless a correction task explicitly assigns it.

### Output and cleanup policy

All disposable output MUST be under
C:\Users\mdbaa\development\Agents\server-agents\harness\.agent-work:

- runs/<run-id>/<agent>/tmp/
- runs/<run-id>/<agent>/logs/
- runs/<run-id>/<agent>/reports/
- runs/<run-id>/<agent>/scratch/
- cache/<tool>/

Use scripts/Invoke-AgentCommand.ps1 for commands that need centralized
temporary paths, logs, reports, or cache variables. It derives paths from its
own location, scopes environment changes to the child process, preserves
argument boundaries and exit codes, and avoids Python bytecode. Use
scripts/Clean-AgentWork.ps1 for preview-first cleanup. Never use git clean -fdx,
broad repository cleanup, or deletion of models, specs, Graphify output, code,
permanent tests, or active runs.

The existing Graphify hook in .codex/hooks.json is preserved. The harness graph
is maintained at harness/graphify-out/graph.json by explicit updates. A future
app graphify update MUST target the app directory explicitly and be coordinated
by the orchestrator.
