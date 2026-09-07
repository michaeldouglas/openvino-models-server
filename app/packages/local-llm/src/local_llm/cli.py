from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from dataclasses import asdict
from typing import Any

from local_llm.config import Settings
from local_llm.core.model_manifest import ModelManifest, configured_manifests


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="local-llm")
    subparsers = parser.add_subparsers(dest="command", required=True)
    models = subparsers.add_parser("models", help="Inspect configured local models")
    model_commands = models.add_subparsers(dest="models_command", required=True)
    model_commands.add_parser("list", help="List configured model aliases")
    info = model_commands.add_parser("info", help="Show one model manifest")
    info.add_argument("alias")
    serve = subparsers.add_parser("serve", help="Run the local HTTP API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--model", help="Default model alias for this process")
    return parser


def _manifest_payload(manifest: ModelManifest) -> dict[str, Any]:
    values = asdict(manifest)
    values["devices"] = list(values["devices"])
    if values["path"] is not None:
        values["path"] = str(values["path"])
    return values


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    settings = Settings()
    manifests = configured_manifests(settings)
    if args.command == "models":
        if args.models_command == "list":
            print(json.dumps([_manifest_payload(item) for item in manifests], indent=2))
            return 0
        selected = next((item for item in manifests if item.alias == args.alias), None)
        if selected is None:
            print(f"Modelo não configurado: {args.alias}")
            return 2
        print(json.dumps(_manifest_payload(selected), indent=2))
        return 0
    if args.model:
        if args.model not in {item.alias for item in manifests}:
            print(f"Modelo não configurado: {args.model}")
            return 2
        os.environ["OVMS_DEFAULT_MODEL"] = args.model
    import uvicorn

    uvicorn.run("local_llm.main:app", host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
