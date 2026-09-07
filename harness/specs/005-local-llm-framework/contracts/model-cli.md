# Contract: Local model CLI

The installed package exposes a `local-llm` command with these MVP commands:

```text
local-llm models list
local-llm models info <alias>
local-llm serve --model <alias> --device <device> --port <port>
local-llm benchmark --model <alias> --prompt-tokens <n> --output-tokens <n>
```

The CLI must fail with actionable messages when a model manifest is missing,
the model directory is incomplete, or the requested device is unavailable. It
must not download arbitrary paths or place weights inside the Python package.
