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

### Feature branches and confirmation gates

Before starting a new feature, the orchestrator MUST report the current
branch and ask exactly:

    Deseja criar uma nova branch de feature para esta tarefa? Sugestão: feature/<nome-descritivo>. Se não, continuarei na branch atual.

This question is asked once for the feature, before branch creation or other
feature changes. The same gate applies to harness configuration work. A
confirmation creates `feature/<nome-descritivo>` from an updated
`origin/develop`; it must not silently continue on `main` or `develop`. A
rejected branch request may continue only on an already suitable work branch.
Never switch branches, discard changes, or stash automatically. Inspect and
preserve dirty changes before any branch transition. Reuse an existing feature
branch only after checking its history and relationship to the requested
feature.

Use `scripts/New-FeatureBranch.ps1` for the confirmation-gated operation. The
wrapper derives the shared Git root from its own location, fetches
`origin/develop`, validates the base, and uses only standard Git operations.
It refuses to mutate state without `-Confirmed` and refuses a dirty checkout.
The principal is the only agent allowed to coordinate branches, commits,
pushes, or pull requests.

### Spec Kit, commits, push and pull requests

The orchestrator owns the Spec Kit sequence and the association between
feature, spec, tasks, commit, branch, and PR. The installed
`.specify/scripts/powershell/create-new-feature.ps1` creates the numbered
`specs/<number>-<slug>` artifacts and `.specify/feature.json`; it does not
create or switch Git branches. Run it only after the branch decision and keep
the feature branch name (`feature/<slug>`) in the surrounding work record and
PR description. Do not duplicate an existing spec or planning artifact.

After implementation and applicable checks, the principal reviews the diff
for secrets, temporary files, models, and unrelated changes, stages only
pertinent files, and creates local commits. It then asks exactly:

    Posso fazer o push da branch <branch> para o repositório michaeldouglas/openvino-models-server e abrir ou atualizar o PR para develop?

Wait for an explicit answer. Without that answer, keep changes local; do not
publish by Git, MCP, API, or another tool. Each new push needs a new
confirmation unless the user explicitly authorizes multiple pushes in a named
scope. Never force-push, publish extra branches, or let a subagent publish
independently.

The repository workflows live at the shared root
`C:/Users/mdbaa/development/Agents/server-agents/.github/workflows/`, not in
`app`. `ensure-feature-pr.yml` idempotently creates or reuses one PR from
`feature/**` to `develop` when the branch has differences. After a PR is
actually merged into `develop`, `promote-develop-to-main.yml` creates or
updates the single PR from `develop` to `main`; it never approves, enables
auto-merge, or merges. `pr-branch-policy.yml` validates the source and target
branches, and `harness-validation.yml` supplies the `validate-harness` check.
The Actions setting that permits workflows to create pull requests is separate
from local MCP credentials and must be verified on GitHub before claiming the
automation is active.

The user-owned rulesets currently report `main` and `develop` as protected via
the available GitHub branch inspection. Exact ruleset requirements and
required-check configuration are not exposed by the installed MCP tools; do
not claim those administrative details are verified until GitHub exposes them
or the user checks them in the repository settings. Require only checks that
actually exist and have run.

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
  python-type-safety, python-testing-patterns, python-design-patterns, and
  refactoring-guru-techniques; consults the relevant skills when creating
  components, defining interfaces, or refactoring. Prioritizes KISS, single
  responsibility, composition, and low coupling. Introduces patterns only for
  concrete problems, briefly explaining the choice, and preserves behavior
  during refactors unless a change is requested.
- platform-engineer: Docker, configuration, device access, model persistence,
  health checks, and CI. Uses docker; the requested github-actions-templates
  skill is not installed and MUST be reported before any CI work. Uses the
  OpenVINO Model Server skill only when OVMS is selected. It may prepare
  metadata-only workflows and validation, but cannot publish, change remote
  protections, or use write credentials to execute feature code.
- quality-reviewer: independent findings-first review of behavior, security,
  tests, lint, typing, and evidence. Uses code-review-excellence,
  ruff-recursive-fix, python-testing-patterns, python-type-safety,
  refactoring-guru-techniques, python-design-patterns, and
  python-anti-patterns to identify code smells, antipatterns, duplication,
  coupling, and unnecessary abstractions. Each finding must include file,
  symbol, impact, and correction suggestion; it also checks whether patterns
  were introduced without need. It may write temporary test outputs under its
  exclusive work directory, but MUST NOT edit application code unless a
  correction task explicitly assigns it.

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

### Branch/workflow operating record

For every feature, record the branch decision, Spec Kit feature path, allowed
files, validation evidence, commit IDs, and PR URL under the run's exclusive
`.agent-work` reports directory. A feature PR targets `develop` and must come
from the same repository under the permitted `feature/` namespace. A promotion
PR targets `main` and must come exclusively from `develop`. Do not create an
empty PR or treat a review approval/closure as a merge.
