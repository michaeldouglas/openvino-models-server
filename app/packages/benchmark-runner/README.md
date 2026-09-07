# Local LLM benchmark runner

This service owns GuideLLM execution and all benchmark reports. It is not part
of the API runtime package. Results are written under `results/<run-id>/` and
are mounted into the container as `/results`.

Run the service through the single `app/runtime/deployment/compose.yaml` file
with the `benchmark-api` profile. The runner validates OVMS before starting
GuideLLM and returns a failed job when no successful measurements are produced.
The same Compose entrypoint already starts the fast 1.7B API configuration.

For a repeatable model/concurrency matrix, run from `app/` after the API and
the `benchmark-api` profile are ready:

```powershell
.\packages\benchmark-runner\scripts\run-matrix.ps1 `
  -Models qwen3-1.7b,qwen3-8b -Concurrencies 1,2 -OutputTokens 32,128 -Requests 10
```

The matrix summary is stored under `packages/benchmark-runner/results/matrix-*` and
records TTFT, latency, output tokens/s and errors. Individual GuideLLM reports
remain in their own run directories.

Use `-ProfileName fast -Device GPU -WarmupRequests 2` to label a fast-profile
run and warm the selected model before collecting samples. Compare identical
prompt/output/concurrency values and inspect Docker resource snapshots saved
next to the matrix report.
