---
name: intel-hardware-advisor
description: Inspect a local Windows, Linux, or macOS inference environment, discover OpenVINO runtime visibility and lightweight device-configuration signals, and provide evidence-aware Intel hardware guidance without inventing compatibility or performance claims.
---

# Intel Hardware Advisor

Use this skill when a user needs to understand the local inference environment
before selecting an Intel execution path. It is designed for first diagnosis:
read-only discovery, explicit uncertainty, and safe next steps.

## Use

When this skill is activated, invoke the bundled
`scripts/hardware_probe.py` yourself. Resolve that path relative to the
directory containing this `SKILL.md`; do not assume the user's current
working directory. Use `--format json` as the stable interface and interpret
the report before answering. Use text output only as a human-friendly view of
the same report.

Do not ask the user to change directories, locate the script, or run the
probe manually. The skill owns discovery and should run the probe whenever the
request requires current local hardware or runtime facts.

## Interpret it

1. Read `collection_status` first. `partial`, `unavailable`, `unsupported`,
   and `failed` are valid outcomes, not reasons to fill in missing facts.
2. Separate `platform` facts from `runtime` facts. A host operating system or
   runtime-visible device does not establish support for a specific workload.
3. For device-specific questions, inspect `runtime.additional_configurations`.
   It reports lightweight read-only indicators for GPU, NPU, GenAI, OpenCV, and
   the execution context. `configured` is not a compatibility guarantee;
   `incomplete`, `not_checked`, and `not_applicable` must remain visible.
4. Follow each fact's `evidence_ids` into `evidence`. Keep detected,
   documented, measured, estimated, and inferred information distinct.
5. Use `recommendation` only within its stated confidence and rationale.
   `decision: no_decision` is required when evidence is absent, conflicting,
   stale, or outside the relevant version and hardware scope.

## Safety boundaries

- Discovery is read-only and does not install packages, change drivers, run
  benchmarks, or scan arbitrary files.
- OpenVINO is optional. Its absence does not prove that the host has no Intel
  hardware, and its device list does not prove model or precision support.
- Additional-configuration checks never install drivers, source `setupvars`,
  change environment variables, or prove that a workload is supported.
- Never claim compatibility, throughput, latency, memory savings, or a
  supported precision from a device name alone.
- Do not request, print, or persist credentials, tokens, serial numbers, user
  names, environment dumps, or unrelated filesystem contents.
- When a user asks for a stronger claim, ask for version- and scope-matched
  authoritative documentation or a reproducible measurement.
- This skill is standalone: it must produce its diagnostic from local
  evidence without requiring another skill, the harness, or project files.
  `intel-docs-reader` is optional enrichment only when the user wants a
  deeper version- and scope-matched interpretation of official OpenVINO
  support, setup, or driver documentation. Its absence must not block or
  invalidate this report.

## Maintainer validation

The project runs this skill with sanitized fixtures. A fixture is a test input,
not a runtime dependency of the promoted skill:

```text
python scripts/hardware_probe.py --fixture <fixture.json> --format json
```

The release candidate must remain self-contained when copied to the sibling
`skills/` directory. Promotion requires the project quality gates and a
read-only review.
