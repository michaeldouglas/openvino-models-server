---
name: intel-openvino-model-server
description: Plan, start, and verify local OpenVINO Model Server deployments with Docker, model repositories, health checks, APIs, and explicit resource boundaries.
---

# Intel OpenVINO Model Server

Use this skill when a user wants to serve OpenVINO models locally, especially
through a Docker-based OpenVINO Model Server test.

## Workflow

1. Invoke `scripts/model_server.py` relative to this `SKILL.md`.
2. Begin with plan mode and JSON output. Show image/version, model repository,
   model versions, volumes, ports, device context, and health/API checks.
3. Do not invent image tags or download assets when the documented version is
   unknown; report the missing evidence.
4. Ask for explicit confirmation before starting containers or writing server
   configuration.
5. Verify container state, server health, model loading, endpoint behavior, and
   metrics separately.

## Boundaries

- Never delete existing containers, model repositories, or volumes by default.
- The first workflow is local/Docker validation, not Kubernetes provisioning.
- Do not expose tokens or publish endpoints without an explicit user request.
- Read `references/server-workflows.md` for repository and API routing.
