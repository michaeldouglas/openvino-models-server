---
name: intel-openvino-benchmark
description: Measure and compare OpenVINO model latency and throughput with reproducible device, batch, iteration, and performance configurations.
---

# Intel OpenVINO Benchmark

Use this skill when a user asks how fast an OpenVINO model runs or wants a
measured comparison between devices or runtime configurations.

## Workflow

1. Invoke `scripts/benchmark_runner.py` relative to this `SKILL.md`.
2. Start with plan mode and JSON output. Make model, device, batch, warmup,
   iterations, streams, and performance hint explicit.
3. Run the benchmark only after the user confirms any requested execution.
4. Report raw measurements, configuration, tool status, variance/limitations,
   and comparison results separately.

## Evidence boundaries

- A benchmark is valid only for the recorded model, runtime, hardware,
  configuration, and workload.
- Do not turn one local measurement into a universal hardware recommendation.
- Do not benchmark while installing drivers or changing BIOS/global settings.
- Read `references/benchmark-methodology.md` when designing comparisons.
