---
name: intel-openvino-inference-runner
description: Compile and run OpenVINO models locally or in Docker while reporting device selection, model compatibility, inference status, and unresolved prerequisites.
---

# Intel OpenVINO Inference Runner

Use this skill when a user wants to execute an OpenVINO model, test a model on
available Intel devices, or validate a Docker inference workspace.

The skill is standalone. It does not require another published skill, the
harness, or an internal documentation path.

## Workflow

1. Invoke `scripts/inference_runner.py` relative to this `SKILL.md`.
2. Begin with plan mode and JSON output. Include model path, device mode,
   execution context, and `--compile-only` when the user supplied them.
3. Report available devices, requested mode, effective device, model inputs and
   outputs, container/volume actions, and blockers.
4. Ask for confirmation before starting a Docker container or writing outputs.
5. Apply the plan, then verify runtime import, model compilation, inference,
   and device visibility as separate results.

## Device and safety rules

- Support explicit devices plus `AUTO`, `MULTI`, and `HETERO` profiles.
- Do not install drivers, modify BIOS, or infer model compatibility from a
  device name alone.
- A successful runtime import is not a successful model compilation.
- A successful compilation is not a performance or accuracy claim.
- Read `references/inference-modes.md` only when device-mode details are needed.
