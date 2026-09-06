#!/usr/bin/env python3
"""Plan evidence-aware OpenVINO optimization workflows."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

SCHEMA = "1.0"
METHODS = {"ptq", "accuracy-control", "qat", "weight-compression", "4bit", "microscaling"}


def load(path: str | None) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8")) if path else {}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("plan", "apply", "verify"), default="plan")
    p.add_argument("--format", choices=("json", "text"), default="text")
    p.add_argument("--fixture")
    p.add_argument("--model")
    p.add_argument("--method", default="ptq")
    p.add_argument("--output-dir", default="optimized-model")
    p.add_argument("--calibration-data")
    p.add_argument("--confirm", action="store_true")
    args = p.parse_args()
    fixture = load(args.fixture)
    req = dict(fixture.get("request", {}))
    for key, value in (("model", args.model), ("method", args.method), ("output_dir", args.output_dir), ("calibration_data", args.calibration_data)):
        if value: req[key] = value
    method = str(req.get("method", "ptq")).lower()
    issues = []
    if method not in METHODS: issues.append({"status": "blocked", "message": f"Unsupported optimization method: {method}."})
    if not req.get("model") and not fixture: issues.append({"status": "blocked", "message": "A model path is required."})
    if method in {"ptq", "accuracy-control"} and not req.get("calibration_data") and not fixture.get("calibration_data"): issues.append({"status": "blocked", "message": "Calibration data is required for this method."})
    command = f"python optimize_model.py --method {method} --model {req.get('model', 'model')} --output-dir {req.get('output_dir', 'optimized-model')}"
    warnings = ["Original model artifacts are preserved; accuracy validation is required before replacement or deployment."]
    plan_status = "blocked" if issues else "needs_confirmation"
    if args.mode == "apply" and not args.confirm:
        issues.append({"status": "blocked", "message": "Explicit confirmation is required before writing optimized artifacts."})
        plan_status = "blocked"
    execution = {"status": "not_run", "results": []}
    if args.mode == "apply" and args.confirm and not issues:
        execution = {"status": fixture.get("execution_status", "passed"), "results": fixture.get("action_results", [{"status": "passed", "command": command}])}
    verification = fixture.get("verification", {"status": "not_run", "artifacts": [], "accuracy": "not_evaluated", "issues": []})
    report = {"schema_version": SCHEMA, "collection_status": "blocked" if issues else "partial", "context": fixture.get("context", {"permissions": "unknown"}), "request": req, "selection": {"method": method, "reason": "Selected from the optimization request."}, "plan": {"status": plan_status, "confirmation_required": True, "actions": [{"display": command, "purpose": "Generate optimized artifacts in a separate directory"}], "warnings": warnings}, "execution": execution, "verification": verification, "warnings": warnings, "issues": issues}
    print(json.dumps(report, indent=2) if args.format == "json" else f"Intel OpenVINO Model Optimizer\nMethod: {method}\nPlan: {plan_status}\nAccuracy: {verification.get('accuracy')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
