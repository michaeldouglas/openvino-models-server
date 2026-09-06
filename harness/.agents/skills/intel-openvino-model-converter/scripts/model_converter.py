#!/usr/bin/env python3
"""Plan and verify OpenVINO model conversion without hiding prerequisites."""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCHEMA = "1.0"
FRAMEWORKS = {"pytorch", "onnx", "tensorflow", "keras", "paddlepaddle", "jax", "tflite"}


def redact(value: object) -> str:
    text = str(value or "")
    text = re.sub(r"(?i)(token|password|secret|api[_-]?key)=\S+", r"\1=<redacted>", text)
    return "\n".join(line[:500] for line in text.splitlines())[:4000]


def load_fixture(path: str | None) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8")) if path else {}


def detect_context(fixture: dict) -> dict:
    if fixture.get("context"):
        return fixture["context"]
    return {
        "system": platform.system(),
        "architecture": platform.machine() or "unknown",
        "permissions": "available" if os.access(Path.cwd(), os.W_OK) else "limited",
        "available_tools": {name: bool(shutil.which(name)) for name in ("python", "pip")},
    }


def infer_framework(model: str) -> str | None:
    suffix = Path(model).suffix.lower()
    return {".onnx": "onnx", ".pt": "pytorch", ".pth": "pytorch", ".pb": "tensorflow", ".tflite": "tflite"}.get(suffix)


def action(argv: list[str], purpose: str) -> dict:
    return {"argv": argv, "display": " ".join(argv), "purpose": purpose}


def build_report(args: argparse.Namespace, fixture: dict) -> dict:
    context = detect_context(fixture)
    request = dict(fixture.get("request", {}))
    if args.framework:
        request["framework"] = args.framework
    if args.model:
        request["model"] = args.model
    if args.output_dir:
        request["output_dir"] = args.output_dir
    if args.shape:
        request["input_shapes"] = args.shape
    model = str(request.get("model") or "model").strip()
    framework = str(request.get("framework") or infer_framework(model) or "").lower()
    issues: list[dict] = []
    warnings: list[str] = []
    if framework not in FRAMEWORKS:
        issues.append({"status": "blocked", "message": "A supported source framework is required."})
    if not request.get("model") and not fixture:
        issues.append({"status": "blocked", "message": "A source model path is required."})
    output_dir = str(request.get("output_dir") or "openvino-model")
    actions: list[dict] = []
    if not issues:
        code = "import sys, openvino as ov; ov.save_model(ov.convert_model(sys.argv[1]), sys.argv[2])"
        actions.append(action([sys.executable, "-c", code, model, output_dir], f"Convert {framework} model to OpenVINO IR"))
        if request.get("input_shapes"):
            warnings.append("Input shapes were requested; verify the converted model inputs before inference.")
    plan_status = "blocked" if issues else "needs_confirmation"
    if args.mode == "apply" and not args.confirm:
        issues.append({"status": "blocked", "message": "Explicit confirmation is required before writing converted artifacts."})
        plan_status = "blocked"
    execution = {"status": "not_run", "results": []}
    if args.mode == "apply" and args.confirm and not issues:
        if fixture.get("action_results") is not None:
            execution = {"status": fixture.get("execution_status", "passed"), "results": fixture["action_results"]}
        else:
            results = []
            for item in actions:
                try:
                    completed = subprocess.run(item["argv"], capture_output=True, text=True, check=False)
                    results.append({"status": "passed" if completed.returncode == 0 else "failed", "command": item["display"], "returncode": completed.returncode, "output": redact(completed.stdout or completed.stderr)})
                except OSError as exc:
                    results.append({"status": "failed", "command": item["display"], "output": redact(exc)})
            execution = {"status": "passed" if results and all(x["status"] == "passed" for x in results) else "failed", "results": results}
    verification = fixture.get("verification", {"status": "not_run", "artifacts": [], "issues": []})
    if args.mode == "verify" and not fixture.get("verification"):
        files = [str(p) for p in Path(output_dir).glob("*")] if Path(output_dir).exists() else []
        verification = {"status": "passed" if files else "failed", "artifacts": files, "issues": [] if files else ["No conversion artifacts were found."]}
    return {"schema_version": SCHEMA, "collection_status": "partial" if warnings else ("blocked" if issues else "complete"), "context": context, "request": request, "selection": {"framework": framework or None, "reason": "Selected from the request or source extension."}, "plan": {"status": plan_status, "confirmation_required": bool(actions), "actions": [{k: v for k, v in item.items() if k != "argv"} for item in actions], "warnings": warnings}, "execution": execution, "verification": verification, "warnings": warnings, "issues": issues}


def render(report: dict) -> str:
    return "Intel OpenVINO Model Converter\n" + json.dumps(report, indent=2) if report.get("format") == "json" else "Intel OpenVINO Model Converter\nPlan: {}\nFramework: {}\nStatus: {}".format(report["plan"]["status"], report["selection"].get("framework"), report["collection_status"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("plan", "apply", "verify"), default="plan")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--fixture")
    parser.add_argument("--framework")
    parser.add_argument("--model")
    parser.add_argument("--output-dir")
    parser.add_argument("--shape")
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    report = build_report(args, load_fixture(args.fixture))
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(f"Intel OpenVINO Model Converter\nPlan: {report['plan']['status']}\nFramework: {report['selection'].get('framework')}\nCollection: {report['collection_status']}")
        for item in report["plan"]["actions"]:
            print(f"- {item['display']}")
        for issue in report["issues"]:
            print(f"Issue: {issue['message']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
