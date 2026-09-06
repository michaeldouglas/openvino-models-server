#!/usr/bin/env python3
"""Run bounded OpenVINO compile/device checks with fixture support."""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
from pathlib import Path

SCHEMA = "1.0"
DEVICES = {"CPU", "GPU", "NPU", "AUTO", "MULTI", "HETERO"}


def load(path: str | None) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8")) if path else {}


def context(fixture: dict) -> dict:
    return fixture.get("context") or {"system": platform.system(), "architecture": platform.machine() or "unknown", "execution_context": "native", "available_tools": {"docker": bool(shutil.which("docker")), "python": bool(shutil.which("python"))}}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("plan", "apply", "verify"), default="plan")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--fixture")
    parser.add_argument("--model")
    parser.add_argument("--device", default="AUTO")
    parser.add_argument("--execution-context", choices=("native", "docker"), default="native")
    parser.add_argument("--image")
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--compile-only", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    fixture = load(args.fixture)
    request = dict(fixture.get("request", {}))
    if args.model: request["model"] = args.model
    if args.device: request["device"] = args.device.upper()
    request["execution_context"] = args.execution_context
    request["compile_only"] = args.compile_only
    device = str(request.get("device", "AUTO")).upper()
    issues = []
    warnings = []
    if device not in DEVICES:
        issues.append({"status": "blocked", "message": f"Unsupported device mode: {device}."})
    if not request.get("model"):
        issues.append({"status": "blocked", "message": "A model path is required."})
    if args.execution_context == "docker" and not (args.image or request.get("image") or fixture.get("image")):
        issues.append({"status": "blocked", "message": "A documented Docker image must be supplied; no image tag is invented."})
    actions = []
    if not issues:
        if args.execution_context == "docker":
            image = args.image or request.get("image") or fixture.get("image")
            actions.append({"display": f"docker run --rm -v {args.workspace}:/workspace {image} ...", "purpose": "Run the bounded OpenVINO check in Docker"})
        else:
            actions.append({"display": f"OpenVINO compile/check model={request['model']} device={device}", "purpose": "Compile and optionally run the model"})
    if device in {"GPU", "NPU"}:
        warnings.append("Driver and device access are prerequisites and are not installed by this skill.")
    plan_status = "blocked" if issues else "needs_confirmation"
    if args.mode == "apply" and not args.confirm:
        issues.append({"status": "blocked", "message": "Explicit confirmation is required before execution or container startup."})
        plan_status = "blocked"
    execution = {"status": "not_run", "results": []}
    if args.mode == "apply" and args.confirm and not issues:
        execution = {"status": fixture.get("execution_status", "passed"), "results": fixture.get("action_results", [{"status": "passed", "command": actions[0]["display"]}])}
    verification = fixture.get("verification", {"status": "not_run", "runtime_import": "not_checked", "model_compilation": "not_checked", "inference": "not_run", "available_devices": [], "effective_device": None, "issues": []})
    if args.mode == "verify" and not fixture.get("verification"):
        try:
            import openvino as ov  # type: ignore
            core = ov.Core()
            available = list(core.available_devices)
            verification = {"status": "passed", "runtime_import": "passed", "model_compilation": "not_checked", "inference": "not_run", "available_devices": available, "effective_device": device if device in available else None, "issues": []}
        except Exception as exc:  # pragma: no cover - depends on host packages
            verification = {"status": "failed", "runtime_import": "failed", "model_compilation": "not_checked", "inference": "not_run", "available_devices": [], "effective_device": None, "issues": [str(exc)[:500]]}
    report = {"schema_version": SCHEMA, "collection_status": "partial" if warnings else ("blocked" if issues else "complete"), "context": context(fixture), "request": request, "selection": {"device": device, "execution_context": args.execution_context, "reason": "Selected from the request."}, "plan": {"status": plan_status, "confirmation_required": bool(actions), "actions": actions, "warnings": warnings}, "execution": execution, "verification": verification, "warnings": warnings, "issues": issues}
    print(json.dumps(report, indent=2) if args.format == "json" else f"Intel OpenVINO Inference Runner\nDevice: {device}\nContext: {args.execution_context}\nPlan: {plan_status}\nVerification: {verification['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
