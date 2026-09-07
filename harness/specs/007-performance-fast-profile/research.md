# Research: Fast Local LLM Performance Profile

## Decision: Separate the fast deployment profile from the quality profile

The fast profile will load only the Qwen3 1.7B servable. The existing multi-model
profile remains available for quality comparison and explicit model selection.

Rationale: the local host has an Intel Arc 140V with shared memory and Docker
Desktop reports a 16 GB Linux VM. The repository contains approximately 1.13 GB
of 1.7B artifacts and 4.55 GB of 8B artifacts. Loading both models increases
startup time and memory pressure even when the default request uses only 1.7B.

## Decision: Keep cache and prefix caching enabled, make capacity tunable

The existing compiled-model cache mount and `enable_prefix_caching` are retained.
Concurrency and sequence capacity are explicit profile settings, with validation
and benchmark comparison rather than an assumed universal optimum.

The Qwen3 1.7B graph currently uses `max_num_seqs=4` while the API defaults to
`MAX_CONCURRENCY=2`; the feature will make this relationship visible and testable.

## Decision: Measure TTFT and generation throughput separately

The API will collect request timing without persisting prompts or full responses.
The benchmark will record warmup, iterations, model, device, concurrency, TTFT,
total latency, output tokens, tokens per second, and errors. Streaming is useful
for perceived latency but must not be presented as lower total compute cost.

## Evidence and references

- OVMS documents `cache_dir`, `max_num_seqs`, prefix caching, dynamic split/fuse,
  and text-generation pipeline settings: [Model Server Parameters](https://docs.openvino.ai/2026/model-server/ovms_docs_parameters.html).
- OVMS model cache speeds later model loading, especially on GPU; it does not
  automatically reduce every token-generation cost: [Model Cache](https://docs.openvino.ai/nightly/model-server/ovms_docs_model_cache.html).
- OpenVINO GPU streams can improve parallel request handling, but actual kernel
  parallelism is device-dependent: [GPU Device](https://docs.openvino.ai/2026/openvino-workflow/running-inference/inference-devices-and-modes/gpu-device.html).
- OpenVINO recommends measuring stream/batch choices on the target hardware:
  [Advanced Throughput Options](https://docs.openvino.ai/2026/openvino-workflow/running-inference/optimize-inference/optimizing-throughput/advanced_throughput_options.html).

## Rejected alternatives

- Adding more Uvicorn workers: it does not make OVMS generation faster and can
  duplicate API clients and memory.
- Hard-coding `MAX_CONCURRENCY=4`: it may improve throughput but can worsen
  single-request latency or memory use; it must be an evaluated profile choice.
- Removing the cache: it would make restarts less predictable and contradict the
  current validated deployment behavior.
