# OpenVINO Model Server Workflows

The first release focuses on:

- local Docker startup;
- a model repository with explicit version directories;
- classic model serving;
- health/API verification;
- REST and gRPC endpoint configuration;
- metrics and troubleshooting.

Serving a model successfully does not prove model accuracy or production
security. Kubernetes, TLS, authentication, scaling, and cloud storage require
separate documented decisions.

Official references:

- https://docs.openvino.ai/2026/model-server/ovms_docs_quick_start_guide.html
- https://docs.openvino.ai/2026/model-server/ovms_docs_deploying_server_docker.html
- https://docs.openvino.ai/2026/model-server/ovms_docs_serving_model.html
- https://docs.openvino.ai/2026/model-server/ovms_docs_metrics.html
- https://docs.openvino.ai/2026/model-server/ovms_docs_troubleshooting.html
