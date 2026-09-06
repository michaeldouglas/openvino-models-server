# Harness skills map

Resolved on: 2026-09-06
Skills root: C:\Users\mdbaa\development\Agents\server-agents\harness\.agents\skills
Skill inventory: skills-lock.json

This is a location-and-purpose map, not a copy of any skill instructions. The
orchestrator reads the complete SKILL.md before applying a selected skill.

## Agent routing

| Agent | Installed skill | Resolved path | Purpose |
|---|---|---|---|
| openvino-engineer | intel-hardware-advisor | .agents/skills/intel-hardware-advisor/SKILL.md | Read-only hardware/runtime evidence |
| openvino-engineer | intel-docs-reader | .agents/skills/intel-docs-reader/SKILL.md | Versioned local OpenVINO documentation |
| openvino-engineer | intel-openvino-installer | .agents/skills/intel-openvino-installer/SKILL.md | Plan, confirm and verify runtime installation |
| openvino-engineer | intel-openvino-model-converter | .agents/skills/intel-openvino-model-converter/SKILL.md | Plan and verify model conversion |
| openvino-engineer | intel-openvino-inference-runner | .agents/skills/intel-openvino-inference-runner/SKILL.md | Plan and verify model compilation/inference |
| openvino-engineer | intel-openvino-genai-runner | .agents/skills/intel-openvino-genai-runner/SKILL.md | Plan and verify text/GenAI workflows |
| openvino-engineer | intel-openvino-model-optimizer | .agents/skills/intel-openvino-model-optimizer/SKILL.md | Plan and verify optimization |
| openvino-engineer | intel-openvino-benchmark | .agents/skills/intel-openvino-benchmark/SKILL.md | Reproducible latency/throughput measurement |
| api-engineer | fastapi-templates | .agents/skills/fastapi-templates/SKILL.md | FastAPI structure and lifecycle patterns |
| api-engineer | python-type-safety | .agents/skills/python-type-safety/SKILL.md | Typed Python contracts and checks |
| api-engineer | python-testing-patterns | .agents/skills/python-testing-patterns/SKILL.md | pytest, fixtures, mocks and integration tests |
| platform-engineer | docker | .agents/skills/docker/SKILL.md | Images, Compose, volumes, health and security |
| platform-engineer | github-actions-templates | Not installed | Requested CI skill unavailable; do not invent or reinstall |
| quality-reviewer | code-review-excellence | .agents/skills/code-review-excellence/SKILL.md | Findings-first behavior/security review |
| quality-reviewer | ruff-recursive-fix | .agents/skills/ruff-recursive-fix/SKILL.md | Controlled Ruff analysis and fixes |
| quality-reviewer | python-testing-patterns | .agents/skills/python-testing-patterns/SKILL.md | Test quality and coverage review |
| quality-reviewer | python-type-safety | .agents/skills/python-type-safety/SKILL.md | Static typing review |

## Spec Kit and Graphify

- Spec Kit workflows are installed at .agents/skills/speckit-* and resolve
  templates/scripts from .specify.
- Graphify executable: C:\Users\mdbaa\.local\bin\graphify.exe.
- Graphify version observed: 0.9.48.
- harness/graphify-out/graph.json is now present with local AST extraction and
  deterministic community structure (`cluster-only --no-label --no-viz`; no LLM
  call). It is the canonical local harness graph. The app has no graph because
  it has no implementation to index; when app code exists, the orchestrator
  must run Graphify against the app path explicitly.
- Graphify 0.9.48 supports `.graphifyignore`; harness/.graphifyignore excludes
  generated output, agent work, caches, bytecode, and virtual environments while
  retaining code, specs, and instructions in the graph scope.
