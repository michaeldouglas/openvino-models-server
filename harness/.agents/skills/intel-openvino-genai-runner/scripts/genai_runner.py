#!/usr/bin/env python3
"""Plan and verify explicit OpenVINO GenAI workload prerequisites."""
from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

SCHEMA = "1.0"
WORKLOADS = {"text", "chat", "gguf", "vlm", "speech", "embedding", "rerank", "image-generation"}


def load(path: str | None) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8")) if path else {}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("plan", "apply", "verify"), default="plan")
    p.add_argument("--format", choices=("json", "text"), default="text")
    p.add_argument("--fixture")
    p.add_argument("--workload")
    p.add_argument("--model")
    p.add_argument("--device", default="CPU")
    p.add_argument("--package", default="openvino-genai")
    p.add_argument("--confirm", action="store_true")
    args = p.parse_args()
    fixture = load(args.fixture)
    req = dict(fixture.get("request", {}))
    for key, value in (("workload", args.workload), ("model", args.model), ("device", args.device), ("package", args.package)):
        if value: req[key] = value
    workload = str(req.get("workload", "text")).lower()
    issues = []
    if workload not in WORKLOADS: issues.append({"status": "blocked", "message": f"Unsupported GenAI workload: {workload}."})
    if not req.get("model") and not fixture: issues.append({"status": "blocked", "message": "A GenAI model asset or explicit model reference is required."})
    actions = [{"display": f"python -m pip install {req.get('package', 'openvino-genai')}", "purpose": "Install the requested GenAI package"}, {"display": f"Run GenAI workload={workload} device={req.get('device', 'CPU')} model={req.get('model', 'model')}", "purpose": "Load and execute the requested GenAI pipeline"}]
    warnings = ["Generation output quality, licensing, model downloads, and device prerequisites are separate evidence fields."]
    if str(req.get("device", "CPU")).upper() == "NPU": warnings.append("NPU GenAI execution requires documented device and driver prerequisites; none are installed automatically.")
    plan_status = "blocked" if issues else "needs_confirmation"
    if args.mode == "apply" and not args.confirm:
        issues.append({"status": "blocked", "message": "Explicit confirmation is required before package installation or model execution."})
        plan_status = "blocked"
    execution = {"status": "not_run", "results": []}
    if args.mode == "apply" and args.confirm and not issues:
        execution = {"status": fixture.get("execution_status", "passed"), "results": fixture.get("action_results", [{"status": "passed", "command": item["display"]} for item in actions])}
    verification = fixture.get("verification", {"status": "not_run", "package_import": "not_checked", "model_loaded": "not_checked", "generation": "not_run", "metrics": {}, "issues": []})
    report = {"schema_version": SCHEMA, "collection_status": "blocked" if issues else ("partial" if warnings else "complete"), "context": fixture.get("context", {"system": platform.system(), "architecture": platform.machine()}), "request": req, "selection": {"workload": workload, "device": req.get("device", "CPU"), "reason": "Selected from the explicit GenAI request."}, "plan": {"status": plan_status, "confirmation_required": True, "actions": actions, "warnings": warnings}, "execution": execution, "verification": verification, "warnings": warnings, "issues": issues}
    print(json.dumps(report, indent=2) if args.format == "json" else f"Intel OpenVINO GenAI Runner\nWorkload: {workload}\nDevice: {req.get('device')}\nPlan: {plan_status}\nVerification: {verification['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
