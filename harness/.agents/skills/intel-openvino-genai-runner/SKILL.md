---
name: intel-openvino-genai-runner
description: Plan and verify OpenVINO GenAI workflows for text, chat, GGUF, VLM, speech, embeddings, and image generation with explicit device and asset prerequisites.
---

# Intel OpenVINO GenAI Runner

Use this skill when a user wants to run or validate a generative OpenVINO
workflow rather than a classic model inference.

## Workflow

1. Invoke `scripts/genai_runner.py` relative to this `SKILL.md`.
2. Start with plan mode and JSON output. Identify workload type, model asset,
   package profile, device, and requested generation metrics.
3. Show package, model, license, device, NPU, and memory prerequisites before
   downloading or running anything.
4. Ask for confirmation before installing optional packages, downloading model
   assets, starting containers, or writing generated artifacts.
5. Verify model loading, generation status, output type, and metrics separately.

## Boundaries

- Keep GenAI evidence separate from classic inference and benchmark results.
- Do not claim model quality from a successful generation call.
- Do not download arbitrary models or expose prompts, tokens, or credentials.
- Read `references/genai-workflows.md` for workload-specific routing.
