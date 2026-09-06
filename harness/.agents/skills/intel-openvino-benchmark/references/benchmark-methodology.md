# OpenVINO Benchmark Methodology

Record at least:

- OpenVINO version and device/plugin;
- model artifact and precision;
- input shape, batch, streams, and performance hint;
- warmup and measured iterations;
- latency and throughput units;
- host/container context and unavailable measurements.

Compare like-for-like workloads. Treat first-run compilation, model caching,
thermal behavior, background load, and data preparation as possible confounders.

Official references:

- https://docs.openvino.ai/2026/about-openvino/performance-benchmarks.html
- https://docs.openvino.ai/2026/about-openvino/performance-benchmarks/getting-performance-numbers.html
- https://docs.openvino.ai/2026/get-started/learn-openvino/openvino-samples/benchmark-tool.html
