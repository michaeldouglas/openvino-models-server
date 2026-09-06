# OpenVINO Model Preparation Reference

Use this reference for method selection. It summarizes the versioned OpenVINO
2026 model-preparation workflow without depending on a local documentation
archive.

| Source framework | Profile | Typical output |
|---|---|---|
| PyTorch | `convert_model` or documented export flow | OpenVINO IR |
| ONNX | ONNX conversion profile | OpenVINO IR |
| TensorFlow/Keras | TensorFlow conversion profile | OpenVINO IR |
| PaddlePaddle | Paddle conversion profile | OpenVINO IR |
| JAX | JAX conversion profile | OpenVINO IR |
| TensorFlow Lite | TFLite conversion profile | OpenVINO IR |

Important checks:

- Confirm framework and model format before selecting a command.
- Treat input-shape changes as part of the model artifact contract.
- Keep conversion parameters and package versions in the report.
- Conversion success does not prove accuracy or device performance.

Official references:

- https://docs.openvino.ai/2026/openvino-workflow/model-preparation.html
- https://docs.openvino.ai/2026/openvino-workflow/model-preparation/convert-model-to-ir.html
- https://docs.openvino.ai/2026/openvino-workflow/model-preparation/conversion-parameters.html
