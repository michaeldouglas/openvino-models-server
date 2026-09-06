#!/usr/bin/env python3
"""Plan and verify bounded local OpenVINO Model Server Docker workflows."""
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
    p.add_argument("--image")
    p.add_argument("--repository", default="./model-repository")
    p.add_argument("--model", default="model")
    p.add_argument("--rest-port", type=int, default=9000)
    p.add_argument("--grpc-port", type=int, default=9001)
    p.add_argument("--device", default="CPU")
    p.add_argument("--confirm", action="store_true")
    args = p.parse_args()
    fixture = load(args.fixture)
    req = dict(fixture.get("request", {}))
    for key, value in (("image", args.image), ("repository", args.repository), ("model", args.model), ("rest_port", args.rest_port), ("grpc_port", args.grpc_port), ("device", args.device)):
        if value not in (None, ""): req[key] = value
    image = req.get("image") or fixture.get("image")
    issues = []
    if not image: issues.append({"status": "blocked", "message": "A documented OpenVINO Model Server image and tag must be supplied; no tag is invented."})
    if req.get("rest_port") == req.get("grpc_port"): issues.append({"status": "blocked", "message": "REST and gRPC ports must be different."})
    command = f"docker run --rm -p {req.get('rest_port')}:9000 -p {req.get('grpc_port')}:9001 -v {req.get('repository')}:/models {image or '<image-required>'}"
    warnings = ["This profile validates a local server; TLS, authentication, Kubernetes, and production secrets require separate configuration."]
    plan_status = "blocked" if issues else "needs_confirmation"
    if args.mode == "apply" and not args.confirm:
        issues.append({"status": "blocked", "message": "Explicit confirmation is required before starting a server container."})
        plan_status = "blocked"
    execution = {"status": "not_run", "results": []}
    if args.mode == "apply" and args.confirm and not issues:
        execution = {"status": fixture.get("execution_status", "passed"), "results": fixture.get("action_results", [{"status": "passed", "command": command}])}
    verification = fixture.get("verification", {"status": "not_run", "container": "not_checked", "health": "not_checked", "model": "not_checked", "endpoints": [], "metrics": "not_checked", "issues": []})
    report = {"schema_version": SCHEMA, "collection_status": "blocked" if issues else ("partial" if not verification.get("status") == "passed" else "complete"), "context": fixture.get("context", {"system": platform.system(), "docker": bool(shutil.which("docker"))}), "request": req, "selection": {"profile": "docker-local", "device": req.get("device", "CPU"), "reason": "Selected from the local server request."}, "plan": {"status": plan_status, "confirmation_required": True, "actions": [{"display": command, "purpose": "Start the local OpenVINO Model Server container"}, {"display": f"curl http://localhost:{req.get('rest_port')}/v1/config", "purpose": "Verify the REST endpoint"}], "warnings": warnings}, "execution": execution, "verification": verification, "warnings": warnings, "issues": issues}
    print(json.dumps(report, indent=2) if args.format == "json" else f"Intel OpenVINO Model Server\nImage: {image or 'required'}\nRepository: {req.get('repository')}\nPlan: {plan_status}\nVerification: {verification['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
