# Research: OpenVINO Model Server API

**Date**: 2026-09-06
**Status**: Planning evidence recorded; real model/GPU gate pending

## Environment evidence

The Intel Hardware Advisor probe was executed through the harness runner with
the installed Python 3.13.7 interpreter. It reported Windows 11 native host,
Intel Core Ultra 7 258V, 32 GB class RAM, Intel Arc 140V visible to Windows,
but OpenVINO unavailable and no runtime devices. The collector status was
partial. This proves host detection only; it does not prove Docker GPU access.

Docker diagnostics reported context `desktop-linux`, Docker Server 29.4.3,
Linux amd64 daemon, 8 CPUs and approximately 15.4 GiB available to the VM. No
OVMS image or container was present. WSL2/container device visibility and real
GPU inference remain unverified. The host GPU's shared-memory reporting is not
treated as additional RAM or as proof of dedicated VRAM.

The local Intel Docs Reader archive was unavailable: the skill's reader could
not resolve/download its versioned 2026 cache. Official OpenVINO documentation
was therefore consulted online and this limitation is recorded rather than
simulating local citations.

## Architecture decision

Use two Compose services: FastAPI `api` and OpenVINO Model Server `ovms`.
OVMS owns model loading and GPU execution; the API only sends OpenAI-compatible
chat requests over the internal network. The API does not import OpenVINO or
load model weights. OVMS continuous batching is the reference capability, but
the first validation uses conservative concurrency and reports measured results
before tuning.

The official continuous-batching documentation demonstrates OpenAI-compatible
`/v1/chat/completions`, streaming, and explicit GPU container arguments. The
official target-device documentation specifies `/dev/dxg` and `/usr/lib/wsl`
for Windows hosts using WSL2, while Linux uses `/dev/dri`; these are not
interchangeable. Sources: [continuous batching demo](https://docs.openvino.ai/2026/model-server/ovms_demos_continuous_batching.html),
[target devices](https://docs.openvino.ai/2026/model-server/ovms_docs_target_devices.html).

## Image decision

Plan for `openvino/model_server:2026.3.1-gpu`, a versioned GPU image based on
Ubuntu 24.04. The Docker Hub tag listing currently exposes this tag and its
digest, but the local daemon has not pulled or verified it. The final Compose
file must pin the digest after a supported manifest inspection. The official
release history documents versioned `*-gpu` images; no floating `latest` or
`weekly` tag is used in the final configuration.

## Model candidates

| Candidate | Evidence and trade-off |
|---|---|
| `OpenVINO/Qwen3-1.7B-int4-ov` (recommended) | Official OpenVINO IR, Apache-2.0, INT4 asymmetric compression, group size 128, compatible with OpenVINO >=2025.1.0. Compact starting point with current Qwen3 chat workflow; quality, Portuguese behavior, memory and GPU performance still require measurement. |
| `OpenVINO/Qwen2.5-1.5B-Instruct-int4-ov` | Official OpenVINO IR, Apache-2.0, explicit Instruct variant, INT4 symmetric compression, OpenVINO >=2025.1.0. Conservative fallback if Qwen3 chat-template or output behavior is unsuitable. |
| `OpenVINO/Qwen3-4B-int4-ov` | Official OpenVINO IR, Apache-2.0, INT4 symmetric/AWQ preparation, OpenVINO >=2026.0.0. Potentially better quality at materially higher memory and latency cost. |

The recommendation is only a planning choice: it is not a claim of Portuguese
quality, compatibility with this exact iGPU, or performance. Model cards:
[Qwen3-1.7B](https://huggingface.co/OpenVINO/Qwen3-1.7B-int4-ov),
[Qwen2.5-1.5B-Instruct](https://huggingface.co/OpenVINO/Qwen2.5-1.5B-Instruct-int4-ov),
[Qwen3-4B](https://huggingface.co/OpenVINO/Qwen3-4B-int4-ov).

## Operational decisions

- The model name and revision are application configuration, not request input.
- Persistent model storage is `app/models/`; downloads/preparation must resume,
  validate and reuse artifacts rather than run on every API start.
- The OVMS command must set `--target_device GPU`. CPU fallback, `AUTO` and
  `MULTI` are deliberately excluded from the required GPU path.
- Readiness probes the OVMS model/configuration endpoint and expected model name;
  it never performs generation.
- Sync, async and stream share validation and payload mapping. Async uses an
  `httpx.AsyncClient`; sync blocking I/O is run through FastAPI's threadpool.
- SSE events are normalized to `delta`, `done` and `error`; the API forwards
  deltas rather than generating the full answer and slicing it afterward.

## Explicitly pending evidence

1. WSL2 status, `/dev/dxg` and `/usr/lib/wsl` visibility from the Docker daemon.
2. OVMS image digest and actual startup with the selected model.
3. Model download integrity, loading log and explicit GPU device evidence.
4. Real sync/async/stream responses and cancellation behavior.
5. TTFT, total latency, tokens/s, resource use and controlled concurrency.
