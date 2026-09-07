# Research: Framework local de LLMs

## Decision: Public OpenAI-compatible chat contract

**Rationale**: LangChain documents that `ChatOpenAI` can use a custom `base_url`
for endpoints implementing the OpenAI Chat Completions API. This gives the
framework immediate interoperability without making LangChain a runtime
dependency. A provider-specific LangChain package can be added later when
non-standard reasoning/tool fields need preservation.

**Alternatives considered**:

- A custom LangChain-only class: deferred because it would make the framework
  depend on one orchestration ecosystem.
- Exposing only the existing `/v1/generate/*` contract: rejected for the public
  framework because generic clients would need custom adapters.

## Decision: Provider-neutral contracts plus OVMS adapter

**Rationale**: The existing generation service already separates application
logic from the OVMS HTTP client. We will formalize that boundary with immutable
request/response types and a provider protocol. This preserves behavior and
keeps future native OpenVINO, OpenAI and other adapters replaceable.

**Alternatives considered**:

- A large provider factory hierarchy: rejected as premature abstraction.
- Direct imports of OVMS schemas from API routes: rejected because it leaks
  infrastructure types into public contracts.

## Decision: Benchmark as a separate service and artifact owner

**Rationale**: The benchmark has GuideLLM dependencies, tokenizer mounts,
long-running jobs and report files that do not belong in the API image. It will
remain callable through the API gateway, but its code and results will live
under `services/benchmark`.

**Alternatives considered**:

- Keep the runner under the API root: rejected because API and benchmark have
  divergent lifecycles and dependency manifests.
- Put reports in a shared application `results/`: rejected because ownership is
  ambiguous and reports look like API runtime state.

## Decision: No model-weight optimization in this feature

**Rationale**: Both current artifacts are already INT4 and the recent benchmark
shows a clear model-size/latency trade-off. First measure API compatibility,
streaming and scheduler settings. Any new quantization must preserve originals
and include calibration/accuracy evidence.

**Alternatives considered**:

- Re-quantize the 8B immediately: deferred until a quality set and accuracy
  comparison exist.
- Replace 8B with a smaller model globally: rejected because model choice is a
  user/product policy, not a runtime implementation detail.

## Decision: Performance defaults and experiments

**Rationale**: Keep 1.7B as the default, preserve prefix caching, expose output
limits, and prepare a separately generated 8B variant for `max_num_seqs=2`.
The scheduler experiment must be measured under concurrency; it is not expected
to improve single-request latency automatically.

**Evidence**: The local run on 2026-09-07 measured 1.7B at 0.606 s median
latency/48.9 generated tokens per second and 8B at 1.852 s/17.5 generated
tokens per second for 32 input and 32 output tokens at concurrency 1.

## Official references

- LangChain chat integrations and custom base URLs:
  https://docs.langchain.com/oss/python/integrations/chat
- LangChain custom chat integrations:
  https://docs.langchain.com/oss/javascript/contributing/implement-langchain
- OpenVINO Model Server text generation parameters:
  https://docs.openvino.ai/2026/model-server/ovms_docs_parameters.html
- OpenVINO Model Server LLM reference:
  https://docs.openvino.ai/2026/model-server/ovms_docs_llm_reference.html
- OpenVINO Model Server performance tuning:
  https://docs.openvino.ai/2025/model-server/ovms_docs_performance_tuning.html
