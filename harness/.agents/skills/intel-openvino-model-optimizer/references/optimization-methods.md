# OpenVINO Optimization Methods

| Request | Profile | Required evidence |
|---|---|---|
| Post-training quantization | PTQ | Calibration data and accuracy comparison |
| Accuracy-controlled quantization | Accuracy control | Accuracy target, validation data, accepted tradeoff |
| Quantization-aware training | QAT | Training configuration and evaluation |
| Weight compression | Weight compression | Size/memory comparison and task validation |
| 4-bit or microscaling | Low-bit profile | Supported model path and accuracy evidence |

Optimization is not conversion, inference, or benchmarking. Keep original
artifacts and write outputs into an explicit separate directory.

Official references:

- https://docs.openvino.ai/2026/openvino-workflow/model-optimization.html
- https://docs.openvino.ai/2026/openvino-workflow/model-optimization-guide/quantizing-models-post-training.html
- https://docs.openvino.ai/2026/openvino-workflow/model-optimization-guide/weight-compression.html
