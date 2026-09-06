#!/usr/bin/env python3
"""Plan, apply, and verify documented OpenVINO installation methods."""

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
from typing import Any


SCHEMA_VERSION = "1.0"
DEFAULT_VERSION = "maintenance"
EXACT_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:\.\d+)?$")
SUPPORTED_METHODS = {
    "pip", "archive", "apt", "yum", "zypper", "conda", "brew", "winget",
    "docker", "npm", "vcpkg", "conan", "yocto", "source",
}
TOOL_BY_METHOD = {
    "pip": "python",
    "archive": "curl",
    "apt": "apt-get",
    "yum": "yum",
    "zypper": "zypper",
    "conda": "conda",
    "brew": "brew",
    "winget": "winget",
    "docker": "docker",
    "npm": "npm",
    "vcpkg": "vcpkg",
    "conan": "conan",
    "yocto": "bitbake",
}
METHOD_ECOSYSTEMS = {
    "pip": "python",
    "archive": "system",
    "apt": "system",
    "yum": "system",
    "zypper": "system",
    "conda": "conda",
    "brew": "system",
    "winget": "system",
    "docker": "docker",
    "npm": "node",
    "vcpkg": "cpp",
    "conan": "cpp",
    "yocto": "yocto",
    "source": "source",
}


def _normalize_architecture(value: str | None) -> str:
    normalized = (value or "unknown").lower()
    if normalized in {"amd64", "x86_64", "x64"}:
        return "x86_64"
    if normalized in {"aarch64", "arm64"}:
        return "arm64"
    if normalized in {"armv7", "armv7l", "armhf"}:
        return "armv7"
    return normalized


def _tool_map() -> dict[str, bool]:
    names = {
        "python": "python",
        "pip": "pip",
        "apt-get": "apt-get",
        "yum": "yum",
        "zypper": "zypper",
        "conda": "conda",
        "brew": "brew",
        "winget": "winget",
        "docker": "docker",
        "npm": "npm",
        "vcpkg": "vcpkg",
        "conan": "conan",
        "bitbake": "bitbake",
        "curl": "curl",
        "tar": "tar",
    }
    return {key: bool(shutil.which(command)) for key, command in names.items()}


def _detect_context() -> dict[str, Any]:
    raw_system = platform.system()
    system = {"Darwin": "macOS"}.get(raw_system, raw_system or "unsupported")
    release = platform.release() or None
    execution_context = "native"
    if os.environ.get("WSL_INTEROP") or "microsoft" in (release or "").lower():
        execution_context = "wsl"
    elif Path("/.dockerenv").exists() or os.environ.get("container"):
        execution_context = "container"
    return {
        "system": system,
        "release": release,
        "architecture": _normalize_architecture(platform.machine()),
        "distribution": None,
        "distribution_version": None,
        "execution_context": execution_context,
        "ecosystem": "auto",
        "permissions": "available" if os.access(Path.cwd(), os.W_OK) else "unknown",
        "available_tools": _tool_map(),
    }


def _load_fixture(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("fixture must be a JSON object")
    if "scenarios" in payload:
        raise ValueError("fixture must describe one installation context")
    return payload


def _redact(value: str | None) -> str:
    if not value:
        return ""
    redacted = re.sub(
        r"(?i)(token|password|secret|api[_-]?key)\s*[=:]\s*[^\s,;]+",
        r"\1=[REDACTED]",
        value,
    )
    lines = [line[:500] for line in redacted.splitlines()]
    return "\n".join(lines)[:4000]


def _exact_version(value: str | None) -> bool:
    return bool(value and EXACT_VERSION.fullmatch(value))


def _version_note(version: str) -> str:
    if _exact_version(version):
        if version.startswith("2026."):
            return "Exact version requested; confirm whether this release is development or maintenance before production use."
        return "Exact version requested by the user."
    if version == "maintenance":
        return "Maintenance track requested; package-manager resolution must be verified after installation."
    if version == "latest":
        return "Latest release requested; this may not be a maintenance release."
    return "Version is not pinned."


def _compatible(method: str, context: dict[str, Any]) -> tuple[bool, str | None]:
    system = context.get("system")
    distribution = str(context.get("distribution") or "").lower()
    if method == "apt" and system != "Linux":
        return False, "APT installation is documented for Linux."
    if method == "yum" and system != "Linux":
        return False, "YUM installation is documented for Linux."
    if method == "zypper" and system != "Linux":
        return False, "ZYPPER installation is documented for Linux."
    if method == "brew" and system != "macOS":
        return False, "Homebrew installation profile is scoped to macOS."
    if method == "winget" and system != "Windows":
        return False, "WinGet installation is Windows-only."
    if method == "docker" and system != "Linux":
        return False, "The documented Docker installation page is scoped to Linux."
    if method == "yocto" and system != "Linux":
        return False, "The documented Yocto workflow is Linux-based."
    if method == "apt" and distribution and not any(x in distribution for x in ("ubuntu", "debian")):
        return False, "The APT repository profile is scoped to Ubuntu/Debian-like distributions."
    if method == "yum" and distribution and any(x in distribution for x in ("opensuse", "ubuntu", "debian")):
        return False, "The YUM profile is not the documented path for this distribution."
    return True, None


def _available(method: str, context: dict[str, Any]) -> bool:
    tool = TOOL_BY_METHOD.get(method)
    if method == "archive":
        tools = context.get("available_tools", {})
        return bool(tools.get("curl") or tools.get("tar"))
    if method == "source":
        return True
    return bool(context.get("available_tools", {}).get(tool, False))


def _system_method(context: dict[str, Any]) -> str:
    system = context.get("system")
    distribution = str(context.get("distribution") or "").lower()
    tools = context.get("available_tools", {})
    if system == "Windows" and tools.get("winget"):
        return "winget"
    if system == "macOS" and tools.get("brew"):
        return "brew"
    if system == "Linux":
        if any(x in distribution for x in ("ubuntu", "debian")) and tools.get("apt-get"):
            return "apt"
        if "opensuse" in distribution and tools.get("zypper"):
            return "zypper"
        if tools.get("yum"):
            return "yum"
    return "archive"


def _select_method(context: dict[str, Any], request: dict[str, Any]) -> tuple[str | None, list[str]]:
    issues: list[str] = []
    explicit = str(request.get("method") or "").lower() or None
    ecosystem = str(request.get("ecosystem") or context.get("ecosystem") or "auto").lower()
    if explicit and explicit not in SUPPORTED_METHODS:
        return None, [f"Unsupported installation method: {explicit}."]
    method = explicit
    if not method:
        if ecosystem in {"python", "python3"}:
            method = "pip"
        elif ecosystem == "conda":
            method = "conda"
        elif ecosystem in {"node", "nodejs", "javascript"}:
            method = "npm"
        elif ecosystem in {"cpp", "c++"}:
            method = "vcpkg" if context.get("available_tools", {}).get("vcpkg") else "conan"
        elif ecosystem == "docker":
            method = "docker"
        elif ecosystem == "yocto":
            method = "yocto"
        elif ecosystem == "source":
            method = "source"
        elif ecosystem == "genai":
            method = "npm" if context.get("available_tools", {}).get("npm") else "pip"
        elif ecosystem == "system":
            method = _system_method(context)
        elif context.get("available_tools", {}).get("python"):
            method = "pip"
        else:
            method = _system_method(context)
    compatible, reason = _compatible(method, context)
    if not compatible and reason:
        issues.append(reason)
    if not _available(method, context):
        if method != "source":
            issues.append(f"Required tool for {method} was not detected.")
    if method == "winget" and not _exact_version(str(request.get("version") or "")):
        issues.append("WinGet requires an explicit OpenVINO release identifier before apply mode.")
    return method, issues


def _action(argv: list[str], purpose: str, mutating: bool = True) -> dict[str, Any]:
    return {"argv": argv, "display": " ".join(_quote(part) for part in argv), "purpose": purpose, "mutating": mutating}


def _quote(value: str) -> str:
    return value if re.fullmatch(r"[A-Za-z0-9_./:=+\-\[\]]+", value) else json.dumps(value)


def _package_name(request: dict[str, Any]) -> str:
    components = {str(item).lower() for item in request.get("components", [])}
    extras = [item for item in ("onnx", "tensorflow2") if item in components]
    package = "openvino"
    if extras:
        package += "[" + ",".join(extras) + "]"
    version = str(request.get("version") or DEFAULT_VERSION)
    if _exact_version(version):
        package += f"=={version}"
    return package


def _build_actions(method: str, context: dict[str, Any], request: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    version = str(request.get("version") or DEFAULT_VERSION)
    actions: list[dict[str, Any]] = []
    warnings = [_version_note(version)]
    if method == "pip":
        target = str(request.get("target_dir") or ".openvino-env")
        python = "python"
        venv_python = str(Path(target) / ("Scripts/python.exe" if context.get("system") == "Windows" else "bin/python"))
        actions.extend([
            _action([python, "-m", "venv", target], "Create an isolated Python environment"),
            _action([venv_python, "-m", "pip", "install", "--upgrade", "pip"], "Update Pip inside the isolated environment"),
            _action([venv_python, "-m", "pip", "install", _package_name(request)], "Install OpenVINO Runtime"),
        ])
        if "genai" in {str(item).lower() for item in request.get("components", [])}:
            actions.append(_action([venv_python, "-m", "pip", "install", "openvino-genai"], "Install optional OpenVINO GenAI"))
    elif method == "conda":
        env_name = str(request.get("environment") or "openvino-env")
        package = "openvino" + (f"={version}" if _exact_version(version) else "")
        actions.extend([
            _action(["conda", "create", "--name", env_name, "--yes"], "Create a Conda environment"),
            _action(["conda", "install", "--name", env_name, "--channel", "conda-forge", package, "--yes"], "Install OpenVINO from Conda Forge"),
        ])
    elif method == "apt":
        warnings.append("The Intel APT repository must already be configured or be added during the confirmed plan.")
        actions.extend([_action(["sudo", "apt-get", "update"], "Refresh APT metadata"), _action(["sudo", "apt-get", "install", "openvino"], "Install OpenVINO Runtime from APT")])
    elif method == "yum":
        warnings.append("The Intel YUM repository must be configured before package installation.")
        actions.append(_action(["sudo", "yum", "install", "openvino"], "Install OpenVINO Runtime from YUM"))
    elif method == "zypper":
        warnings.append("The configured Zypper repository must expose OpenVINO packages.")
        actions.extend([_action(["sudo", "zypper", "refresh"], "Refresh Zypper metadata"), _action(["sudo", "zypper", "install", "openvino-devel", "openvino-sample"], "Install OpenVINO development/runtime packages")])
    elif method == "brew":
        actions.append(_action(["brew", "install", "openvino"], "Install OpenVINO with Homebrew"))
    elif method == "winget":
        package_id = f"Intel.OpenVINOToolkit.{version}"
        actions.append(_action(["winget", "install", "--id", package_id, "-e", "--source", "winget"], "Install the versioned OpenVINO package with WinGet"))
    elif method == "npm":
        package = "openvino-node"
        if "genai" in {str(item).lower() for item in request.get("components", [])}:
            package = "openvino-genai-node"
        if _exact_version(version):
            package += f"@{version}"
        actions.append(_action(["npm", "install", package], "Install the OpenVINO Node.js package"))
    elif method == "vcpkg":
        actions.append(_action(["vcpkg", "install", "openvino"], "Install OpenVINO through vcpkg"))
        warnings.append("vcpkg profiles provide the C/C++ API; project integration remains separate.")
    elif method == "conan":
        actions.extend([_action(["python3", "-m", "pip", "install", "conan>=2.0.8"], "Ensure Conan 2 is available"), _action(["conan", "install", "conanfile.txt", "--build", "missing"], "Resolve the OpenVINO Conan dependency")])
        warnings.append("The documented Conan profile does not offer NPU inference.")
    elif method == "docker":
        warnings.append("The OpenVINO Docker documentation points to registry images and accelerator-specific guides; select the image before pulling.")
    elif method == "yocto":
        warnings.append("Yocto requires a project-specific OpenEmbedded configuration; the skill can plan and verify package inclusion but must not alter an arbitrary build tree.")
    elif method == "archive":
        warnings.append("Archive URLs and installation directories are platform/version-specific; an exact release and target directory are required before apply mode.")
    elif method == "source":
        warnings.append("Building from source is an advanced workflow and requires a project-specific build configuration; no source build is executed by default.")
    return actions, warnings


def _verification_from_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    value = fixture.get("verification")
    if isinstance(value, dict):
        return {
            "status": value.get("status", "unknown"),
            "installed_version": value.get("installed_version"),
            "runtime_import": value.get("runtime_import", "not_checked"),
            "devices": value.get("devices", []),
            "components": value.get("components", {}),
            "issues": value.get("issues", []),
        }
    return {"status": "not_run", "installed_version": None, "runtime_import": "not_checked", "devices": [], "components": {}, "issues": []}


def _run_actions(actions: list[dict[str, Any]], fixture: dict[str, Any] | None) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    fixture_results = fixture.get("action_results", []) if fixture else []
    for index, action in enumerate(actions):
        if index < len(fixture_results):
            raw = fixture_results[index]
            result = {"status": raw.get("status", "failed"), "command": action["display"], "output": _redact(raw.get("stdout") or raw.get("stderr"))}
        else:
            try:
                completed = subprocess.run(action["argv"], capture_output=True, text=True, timeout=900, check=False)
                result = {"status": "passed" if completed.returncode == 0 else "failed", "command": action["display"], "returncode": completed.returncode, "output": _redact(completed.stdout or completed.stderr)}
            except (OSError, subprocess.TimeoutExpired) as exc:
                result = {"status": "failed", "command": action["display"], "output": _redact(str(exc))}
        results.append(result)
        if result["status"] != "passed":
            return {"status": "failed", "results": results}
    return {"status": "passed", "results": results}


def _build_report(args: argparse.Namespace) -> dict[str, Any]:
    fixture = _load_fixture(Path(args.fixture)) if args.fixture else None
    context = dict(fixture.get("context", {})) if fixture else _detect_context()
    if not fixture:
        context["available_tools"] = context.get("available_tools", _tool_map())
    request = dict(fixture.get("request", {})) if fixture else {}
    if args.ecosystem:
        request["ecosystem"] = args.ecosystem
    if args.method:
        request["method"] = args.method
    if args.version:
        request["version"] = args.version
    if args.target_dir:
        request["target_dir"] = args.target_dir
    if args.component:
        request["components"] = args.component
    request.setdefault("version", DEFAULT_VERSION)
    method, issues = _select_method(context, request)
    actions: list[dict[str, Any]] = []
    warnings: list[str] = []
    if method:
        actions, warnings = _build_actions(method, context, request)
    blocked = bool(issues)
    plan_status = "blocked" if blocked else "needs_confirmation"
    if not method:
        plan_status = "unsupported"
    selection = {
        "method": method,
        "ecosystem": METHOD_ECOSYSTEMS.get(method) if method else None,
        "version": request.get("version"),
        "reason": "Selected from the detected context and requested ecosystem." if method else None,
        "alternatives": [item for item in ("pip", "archive", "conda") if item != method and (item in SUPPORTED_METHODS)],
    }
    plan = {
        "status": plan_status,
        "confirmation_required": bool(actions),
        "actions": [{key: value for key, value in action.items() if key != "mutating"} for action in actions],
        "warnings": warnings,
    }
    execution = {"status": "not_run", "results": []}
    verification = _verification_from_fixture(fixture or {}) if args.mode == "verify" else {"status": "not_run", "installed_version": None, "runtime_import": "not_checked", "devices": [], "components": {}, "issues": []}
    if args.mode == "apply":
        if not args.confirm:
            issues.append("Apply mode requires --confirm after the user explicitly approves the plan.")
            execution = {"status": "not_run", "results": []}
        elif blocked:
            execution = {"status": "not_run", "results": []}
        else:
            execution = _run_actions(actions, fixture)
            if execution["status"] == "passed":
                verification = _verification_from_fixture(fixture or {})
                if verification["status"] == "not_run":
                    verification["status"] = "partial"
                    verification["runtime_import"] = "not_checked"
                    verification["issues"].append("Runtime installation completed, but live verification data was not supplied.")
    if args.mode == "verify" and not fixture:
        verification = _live_verify(context)
    report = {
        "schema_version": SCHEMA_VERSION,
        "collection_status": "partial" if issues else "complete",
        "context": context,
        "selection": selection,
        "plan": plan,
        "execution": execution,
        "verification": verification,
        "issues": [{"status": "blocked", "message": item} for item in issues],
    }
    return report


def _live_verify(context: dict[str, Any]) -> dict[str, Any]:
    if not context.get("available_tools", {}).get("python"):
        return {"status": "failed", "installed_version": None, "runtime_import": "not_checked", "devices": [], "components": {}, "issues": [{"message": "Python is unavailable for runtime verification."}]}
    try:
        import openvino as ov  # type: ignore

        core = ov.Core()
        return {"status": "passed", "installed_version": getattr(ov, "__version__", None), "runtime_import": "passed", "devices": list(core.available_devices), "components": {}, "issues": []}
    except Exception as exc:  # OpenVINO is an optional runtime.
        return {"status": "failed", "installed_version": None, "runtime_import": "failed", "devices": [], "components": {}, "issues": [{"message": _redact(str(exc))}]}


def _render_text(report: dict[str, Any]) -> str:
    context = report["context"]
    selection = report["selection"]
    plan = report["plan"]
    verification = report["verification"]
    lines = [
        "Intel OpenVINO Installer",
        f"Context: {context.get('system')} {context.get('release') or ''} ({context.get('architecture')}) / {context.get('execution_context')}",
        f"Selected method: {selection.get('method') or 'none'}",
        f"Version: {selection.get('version')}",
        f"Plan: {plan.get('status')} (confirmation required: {plan.get('confirmation_required')})",
        f"Execution: {report['execution'].get('status')}",
        f"Verification: {verification.get('status')}",
    ]
    if plan.get("actions"):
        lines.append("Actions:")
        lines.extend(f"- {action['display']}" for action in plan["actions"])
    if plan.get("warnings"):
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in plan["warnings"])
    if verification.get("installed_version"):
        lines.append(f"Installed version: {verification['installed_version']}")
    if verification.get("devices"):
        lines.append(f"Devices: {', '.join(verification['devices'])}")
    if report.get("issues"):
        lines.append("Issues:")
        lines.extend(f"- {item['message']}" for item in report["issues"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan, apply, and verify OpenVINO installation")
    parser.add_argument("--mode", choices=("plan", "apply", "verify"), default="plan")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--fixture")
    parser.add_argument("--ecosystem")
    parser.add_argument("--method", choices=sorted(SUPPORTED_METHODS))
    parser.add_argument("--version")
    parser.add_argument("--target-dir")
    parser.add_argument("--component", action="append", default=[])
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    try:
        report = _build_report(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report = {"schema_version": SCHEMA_VERSION, "collection_status": "failed", "context": {}, "selection": {}, "plan": {}, "execution": {"status": "not_run", "results": []}, "verification": {"status": "not_run", "installed_version": None, "runtime_import": "not_checked", "devices": [], "components": {}, "issues": []}, "issues": [{"status": "failed", "message": _redact(str(exc))}]}
    print(json.dumps(report, indent=2, ensure_ascii=False) if args.format == "json" else _render_text(report))
    return 0 if report["collection_status"] != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
