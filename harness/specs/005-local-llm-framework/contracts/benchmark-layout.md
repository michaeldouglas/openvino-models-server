# Contract: Benchmark ownership and layout

The benchmark service owns:

```text
app/services/benchmark/
├── src/benchmark_runner/
├── Dockerfile
├── pyproject.toml
└── results/<run-id>/
    ├── benchmarks.json
    ├── benchmarks.csv
    ├── benchmarks.html
    ├── run-manifest.json
    └── run.log
```

The API may submit, query and proxy report downloads, but it does not import
GuideLLM or write benchmark files directly. The Compose file mounts this
directory to `/results` in the benchmark container.
