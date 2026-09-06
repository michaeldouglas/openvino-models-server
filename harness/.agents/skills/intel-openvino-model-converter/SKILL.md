---
name: intel-openvino-model-converter
description: Prepare supported PyTorch, ONNX, TensorFlow, Keras, PaddlePaddle, or JAX models for OpenVINO with a documented, confirmation-gated conversion plan.
---

# Intel OpenVINO Model Converter

Use this skill when a user needs to convert a source model into OpenVINO IR or
prepare its input shapes for later inference.

The skill is standalone. It does not require the hardware advisor, docs reader,
installer, harness, or any project file outside this folder.

## Workflow

1. Invoke the bundled `scripts/model_converter.py` relative to this `SKILL.md`.
2. Start with `--mode plan --format json` and provide the source framework,
   model path, output directory, and input shapes when known.
3. Explain the selected conversion profile, prerequisites, output artifacts,
   and unresolved framework or operator limitations.
4. Ask for explicit confirmation before writing generated artifacts.
5. After confirmation, run `--mode apply --confirm`; then run verify mode.
6. Preserve the source model and report conversion success separately from
   inference compatibility, accuracy, and performance.

## Boundaries

- Never delete or replace the source model automatically.
- Never claim all operators are supported without a successful conversion and
  verification result.
- Do not install drivers, change global environments, or download arbitrary
  model assets without the user's request and a visible plan.
- Read `references/model-preparation.md` only when a framework or conversion
  option needs detailed routing.
