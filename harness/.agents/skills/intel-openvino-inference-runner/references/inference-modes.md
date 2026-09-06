# OpenVINO Inference Modes

The runner keeps these concepts separate:

- **Explicit device**: compile on `CPU`, `GPU`, or `NPU` when available.
- **AUTO**: let OpenVINO select an available device according to the runtime
  policy; report the effective device rather than assuming one.
- **MULTI**: use a configured list of devices and report the requested order.
- **HETERO**: split supported model operations across a configured device list;
  compilation and operator support must be verified.
- **Compile-only**: validate model/device compilation without executing user
  inputs.

Additional checks include dynamic shapes, input/output metadata, preprocessing,
performance hints, model caching, and device properties. These are evidence
fields, not automatic compatibility guarantees.

Official references:

- https://docs.openvino.ai/2026/openvino-workflow/running-inference.html
- https://docs.openvino.ai/2026/openvino-workflow/running-inference/inference-devices-and-modes.html
- https://docs.openvino.ai/2026/openvino-workflow/running-inference/inference-devices-and-modes/auto-device-selection.html
- https://docs.openvino.ai/2026/openvino-workflow/running-inference/inference-devices-and-modes/hetero-execution.html
