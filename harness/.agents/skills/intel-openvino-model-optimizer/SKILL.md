---
name: intel-openvino-model-optimizer
description: Plan and verify OpenVINO quantization, weight compression, and accuracy-aware model optimization while protecting original artifacts.
---

# Intel OpenVINO Model Optimizer

Use this skill when a user wants to reduce model size, memory use, or inference
cost through a documented OpenVINO optimization workflow.

## Workflow

1. Invoke `scripts/model_optimizer.py` relative to this `SKILL.md`.
2. Begin with plan mode and JSON output. Specify post-training quantization,
   accuracy-controlled quantization, QAT, weight compression, 4-bit, or
   microscaling when known.
3. Show calibration/validation prerequisites, output directory, and commands.
4. Require explicit confirmation before generating optimized artifacts.
5. Verify optimized artifacts separately and request accuracy evidence before
   any replacement or deployment.

## Boundaries

- Preserve original models by default.
- Never claim accuracy equivalence without an evaluation result.
- Do not silently select a calibration dataset or invent tolerances.
- Do not combine optimization with driver installation or benchmark claims.
- Read `references/optimization-methods.md` for method-specific routing.
