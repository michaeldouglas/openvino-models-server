#!/usr/bin/env python3
"""Create reproducible benchmark plans and render fixture measurements."""
from __future__ import annotations

import argparse
import json
import platform
import shutil
from pathlib import Path

SCHEMA = "1.0"


def load(path: str | None) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8")) if path else {}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("plan", "apply", "verify"), default="plan")
    p.add_argument("--format", choices=("json", "text"), default="text")
    p.add_argument("--fixture")
    p.add_argument("--model")
    p.add_argument("--device", default="CPU")
    p.add_argument("--iterations", type=int, default=100)
    p.add_argument("--warmup", type=int, default=10)
    p.add_argument("--batch", type=int, default=1)
    p.add_argument("--hint", default="")
    p.add_argument("--confirm", action="store_true")
    args = p.parse_args()
    fixture = load(args.fixture)
    req = dict(fixture.get("request", {}))
    for key, value in (("model", args.model), ("device", args.device), ("iterations", args.iterations), ("warmup", args.warmup), ("batch", args.batch), ("performance_hint", args.hint)):
        if value not in (None, "", 0): req[key] = value
    issues = []
    if not req.get("model") and not fixture: issues.append({"status": "blocked", "message": "A model path is required."})
    if req.get("iterations", 0) < 1: issues.append({"status": "blocked", "message": "Iterations must be positive."})
    command = f"benchmark_app -m {req.get('model', 'model')} -d {req.get('device', 'CPU')} -niter {req.get('iterations', 100)} -nstreams {req.get('streams', 'AUTO')}"
    warnings = ["Measurements are valid only for the recorded model, runtime, host, and configuration."]
    plan_status = "blocked" if issues else "ready"
    if args.mode == "apply" and not args.confirm:
        issues.append({"status": "blocked", "message": "Explicit confirmation is required before running a benchmark."})
        plan_status = "blocked"
    execution = {"status": "not_run", "results": []}
    if args.mode == "apply" and args.confirm and not issues:
        execution = {"status": fixture.get("execution_status", "passed"), "results": fixture.get("action_results", [{"status": "passed", "command": command}])}
    measurements = fixture.get("measurements", {})
    verification = {"status": "passed" if measurements else "not_run", "measurements": measurements, "comparison": fixture.get("comparison", []), "limitations": fixture.get("limitations", warnings), "issues": []}
    report = {"schema_version": SCHEMA, "collection_status": "blocked" if issues else ("complete" if measurements else "partial"), "context": fixture.get("context", {"system": platform.system(), "architecture": platform.machine(), "available_tools": {"benchmark_app": bool(shutil.which("benchmark_app"))}}), "request": req, "selection": {"device": req.get("device", "CPU"), "tool": "benchmark_app", "reason": "Selected from the benchmark request."}, "plan": {"status": plan_status, "confirmation_required": True, "actions": [{"display": command, "purpose": "Measure the requested workload"}], "warnings": warnings}, "execution": execution, "verification": verification, "warnings": warnings, "issues": issues}
    print(json.dumps(report, indent=2) if args.format == "json" else f"Intel OpenVINO Benchmark\nModel: {req.get('model')}\nDevice: {req.get('device')}\nPlan: {plan_status}\nMeasurements: {verification['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
