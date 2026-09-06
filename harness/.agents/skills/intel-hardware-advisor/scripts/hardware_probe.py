"""Read-only local hardware/runtime probe with deterministic fixture support."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from report_model import build_report


MAX_OUTPUT = 64_000
ALLOWED_FIXTURE_KEYS = {"fixture_version", "platform", "runtime", "collector_status"}
ALLOWED_PLATFORM_KEYS = {
    "system",
    "release",
    "machine",
    "distribution",
    "distribution_version",
    "kernel",
    "architecture",
    "os_version",
    "context",
    "status",
}
ALLOWED_CONTEXT_KEYS = {"wsl", "container"}
ALLOWED_RUNTIME_KEYS = {"openvino", "additional_configurations"}
ALLOWED_OPENVINO_KEYS = {"status", "version", "devices"}
ALLOWED_DEVICE_KEYS = {"id", "name", "vendor", "type", "status"}
ALLOWED_CONFIGURATION_KEYS = {"gpu", "npu", "genai", "opencv", "environment"}
ALLOWED_CONFIGURATION_ENTRY_KEYS = {"status", "checks", "notes"}
FORBIDDEN_TOKENS = {"password", "secret", "token", "api_key", "username", "user_name", "serial_number"}


def run_command(args: list[str], timeout: float = 2.0) -> dict[str, Any]:
    """Run an explicit command without a shell and return safe metadata only."""
    if not args or not all(isinstance(item, str) and item for item in args):
        return {"status": "failed", "message": "invalid command arguments"}
    try:
        completed = subprocess.run(
            args,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return {"status": "unavailable", "message": "tool is not installed"}
    except subprocess.TimeoutExpired:
        return {"status": "failed", "message": "tool timed out"}
    except PermissionError:
        return {"status": "permission_denied", "message": "tool permission denied"}
    except OSError:
        return {"status": "failed", "message": "tool could not be executed"}
    if completed.returncode != 0:
        return {"status": "failed", "message": "tool returned an error"}
    # The live first release intentionally does not parse arbitrary command output.
    _ = (completed.stdout or "")[:MAX_OUTPUT]
    return {"status": "detected", "message": "tool completed"}


def _normalize_architecture(machine: str | None) -> str | None:
    value = (machine or "").strip().lower()
    if value in {"amd64", "x86_64", "x64"}:
        return "x86_64"
    if value in {"aarch64", "arm64", "arm64-v8a"}:
        return "arm64"
    if value.startswith("armv7") or value in {"arm", "arm32"}:
        return "armv7"
    return machine or None


def _linux_os_release() -> dict[str, str]:
    if platform.system() != "Linux":
        return {}
    try:
        content = Path("/etc/os-release").read_text(encoding="utf-8")[:MAX_OUTPUT]
    except (OSError, UnicodeError):
        return {}
    values: dict[str, str] = {}
    for line in content.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"').strip("'")
    return values


def _is_wsl() -> bool:
    return bool(os.environ.get("WSL_INTEROP")) or "microsoft" in platform.release().lower()


def _is_container() -> bool:
    return Path("/.dockerenv").is_file() or os.environ.get("container", "").lower() in {"docker", "podman"}


def collect_platform() -> dict[str, Any]:
    raw_system = platform.system() or ""
    system = "macOS" if raw_system == "Darwin" else raw_system
    status = "detected" if raw_system in {"Windows", "Linux", "Darwin"} else "unsupported"
    machine = platform.machine() or ""
    linux_release = _linux_os_release()
    if raw_system == "Darwin":
        os_version = platform.mac_ver()[0] or platform.release() or None
    elif raw_system == "Windows":
        os_version = platform.win32_ver()[0] or platform.release() or None
    else:
        os_version = linux_release.get("VERSION_ID") or platform.release() or None
    return {
        "system": system or None,
        "release": platform.release() or None,
        "machine": machine or None,
        "distribution": linux_release.get("ID") or None,
        "distribution_version": linux_release.get("VERSION_ID") or None,
        "kernel": platform.release() if raw_system == "Linux" else None,
        "architecture": _normalize_architecture(machine),
        "os_version": os_version,
        "context": {"wsl": _is_wsl() if raw_system == "Linux" else False, "container": _is_container()},
        "status": status,
    }


def _device_type(device_id: str) -> str:
    token = device_id.upper().replace("-", ".").split(".", 1)[0]
    return token if token in {"CPU", "GPU", "NPU"} else "other"


def collect_openvino() -> dict[str, Any]:
    try:
        import openvino as ov  # type: ignore

        core = ov.Core()
        devices = []
        for device_id in core.available_devices:
            name = device_id
            try:
                name = str(core.get_property(device_id, "FULL_DEVICE_NAME"))[:256]
            except Exception:
                name = device_id
            safe_id = str(device_id)[:64]
            devices.append({"id": safe_id, "name": name, "type": _device_type(safe_id), "status": "detected"})
        return {"status": "available", "version": str(getattr(ov, "__version__", "unknown"))[:64], "devices": devices}
    except ImportError:
        return {"status": "unavailable", "version": None, "devices": []}
    except PermissionError:
        return {"status": "permission_denied", "version": None, "devices": []}
    except Exception:
        return {"status": "failed", "version": None, "devices": []}


def _configuration(status: str, checks: dict[str, str] | None = None, notes: list[str] | None = None) -> dict[str, Any]:
    return {"status": status, "checks": checks or {}, "notes": notes or []}


def _module_status(module_name: str) -> str:
    try:
        return "detected" if importlib.util.find_spec(module_name) else "unavailable"
    except (ImportError, ModuleNotFoundError, ValueError):
        return "unknown"


def _has_device_node(*paths: str) -> str:
    try:
        return "detected" if any(Path(path).exists() for path in paths) else "unavailable"
    except OSError:
        return "unknown"


def collect_additional_configurations(platform_profile: dict[str, Any], openvino_profile: dict[str, Any]) -> dict[str, Any]:
    """Collect small, read-only indicators without external skill dependencies."""
    system = platform_profile.get("system")
    device_types = {
        str(device.get("type") or _device_type(str(device.get("id", "")))).upper()
        for device in openvino_profile.get("devices", [])
        if isinstance(device, dict)
    }
    configurations: dict[str, Any] = {}

    if "GPU" not in device_types:
        configurations["gpu"] = _configuration("not_applicable")
    elif system == "Linux":
        device_nodes = _has_device_node("/dev/dri/renderD128", "/dev/dri/card0")
        configurations["gpu"] = _configuration(
            "incomplete",
            {"device_nodes": device_nodes, "driver": "not_checked", "opencl": "not_checked", "level_zero": "not_checked"},
            ["Device-node presence does not prove driver or workload compatibility."],
        )
    else:
        configurations["gpu"] = _configuration(
            "not_checked",
            {"driver": "not_checked", "opencl": "not_checked", "level_zero": "not_checked"},
            ["Driver verification is platform-specific and was not performed by the portable probe."],
        )

    if "NPU" not in device_types:
        configurations["npu"] = _configuration("not_applicable")
    elif system == "Linux":
        device_nodes = _has_device_node("/dev/accel/accel0", "/dev/vpu0")
        configurations["npu"] = _configuration(
            "incomplete",
            {"device_nodes": device_nodes, "driver": "not_checked", "kernel_headers": "not_checked"},
            ["Device-node presence does not prove driver or workload compatibility."],
        )
    else:
        configurations["npu"] = _configuration(
            "not_checked",
            {"driver": "not_checked", "kernel_headers": "not_checked"},
            ["Driver verification is platform-specific and was not performed by the portable probe."],
        )

    if openvino_profile.get("status") != "available":
        configurations["genai"] = _configuration("not_applicable", notes=["OpenVINO is not available in this profile."])
    else:
        genai = _module_status("openvino_genai")
        tokenizers = _module_status("openvino_tokenizers")
        configurations["genai"] = _configuration(
            "detected" if genai == "detected" and tokenizers == "detected" else "incomplete",
            {"openvino_genai": genai, "openvino_tokenizers": tokenizers, "version_alignment": "not_checked"},
            ["GenAI packages are optional; package version alignment still requires documentation or package metadata."],
        )

    opencv = _module_status("cv2")
    configurations["opencv"] = _configuration(
        "detected" if opencv == "detected" else "unavailable",
        {"python_module": opencv},
        ["OpenCV is optional and is not required for ordinary OpenVINO inference."],
    )
    context = platform_profile.get("context") if isinstance(platform_profile.get("context"), dict) else {}
    configurations["environment"] = _configuration(
        "detected",
        {
            "wsl": "detected" if context.get("wsl") else "not_detected",
            "container": "detected" if context.get("container") else "not_detected",
            "setupvars": "not_checked",
        },
        ["The probe does not modify environment variables or source setup scripts."],
    )
    return configurations


def collect_live() -> dict[str, Any]:
    platform_profile = collect_platform()
    openvino_profile = collect_openvino()
    configurations = collect_additional_configurations(platform_profile, openvino_profile)
    return {
        "platform": platform_profile,
        "runtime": {"openvino": openvino_profile, "additional_configurations": configurations},
        "collector_status": {
            "platform": platform_profile["status"],
            "openvino": "available" if openvino_profile.get("status") == "available" else openvino_profile.get("status"),
            "configurations": "complete",
        },
    }


def _walk_for_forbidden(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower()
            if lowered in FORBIDDEN_TOKENS or any(token in lowered for token in FORBIDDEN_TOKENS):
                return True
            if _walk_for_forbidden(nested):
                return True
    elif isinstance(value, list):
        return any(_walk_for_forbidden(item) for item in value)
    return False


def validate_fixture(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict) or set(payload) != ALLOWED_FIXTURE_KEYS:
        raise ValueError("fixture shape is not allowed")
    if payload.get("fixture_version") != "1":
        raise ValueError("unsupported fixture version")
    if _walk_for_forbidden(payload):
        raise ValueError("fixture contains a forbidden field")
    if not isinstance(payload.get("platform"), dict) or not isinstance(payload.get("runtime"), dict):
        raise ValueError("fixture platform and runtime must be objects")
    if not set(payload["platform"]).issubset(ALLOWED_PLATFORM_KEYS) or not set(payload["runtime"]).issubset(ALLOWED_RUNTIME_KEYS):
        raise ValueError("fixture contains an unknown platform or runtime field")
    context = payload["platform"].get("context")
    if (
        context is not None
        and (
            not isinstance(context, dict)
            or not set(context).issubset(ALLOWED_CONTEXT_KEYS)
            or any(not isinstance(value, bool) for value in context.values())
        )
    ):
        raise ValueError("fixture platform context is malformed")
    openvino = payload["runtime"].get("openvino")
    if not isinstance(openvino, dict) or not set(openvino).issubset(ALLOWED_OPENVINO_KEYS) or not isinstance(openvino.get("devices", []), list):
        raise ValueError("fixture OpenVINO data is malformed")
    for device in openvino.get("devices", []):
        if not isinstance(device, dict) or not set(device).issubset(ALLOWED_DEVICE_KEYS) or not isinstance(device.get("id"), str):
            raise ValueError("fixture device is malformed")
    configurations = payload["runtime"].get("additional_configurations")
    if configurations is not None:
        if not isinstance(configurations, dict) or not set(configurations).issubset(ALLOWED_CONFIGURATION_KEYS):
            raise ValueError("fixture configurations are malformed")
        for entry in configurations.values():
            if not isinstance(entry, dict) or not set(entry).issubset(ALLOWED_CONFIGURATION_ENTRY_KEYS):
                raise ValueError("fixture configuration entry is malformed")
            if not isinstance(entry.get("status"), str):
                raise ValueError("fixture configuration status is malformed")
            if "checks" in entry and not isinstance(entry["checks"], dict):
                raise ValueError("fixture configuration checks are malformed")
            if "notes" in entry and not isinstance(entry["notes"], list):
                raise ValueError("fixture configuration notes are malformed")


def load_fixture(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise ValueError("fixture could not be read") from None
    validate_fixture(payload)
    return payload


def render_text(report: dict[str, Any]) -> str:
    recommendation = report["recommendation"]
    lines = [
        "Intel Hardware Advisor",
        f"Collection status: {report['collection_status']['status']}",
        f"Platform: {report['platform'].get('system')} {report['platform'].get('os_version') or report['platform'].get('release')} ({report['platform'].get('architecture') or report['platform'].get('machine')})",
        f"OpenVINO: {report['runtime']['openvino'].get('status')} {report['runtime']['openvino'].get('version') or ''}".rstrip(),
        f"Recommendation: {recommendation['decision']} (confidence: {recommendation['confidence']})",
        "Rationale:",
    ]
    lines.extend(f"- {item}" for item in recommendation["rationale"])
    lines.append("Evidence:")
    lines.extend(f"- {item['id']}: {item['kind']} from {item['source']}" for item in report["evidence"])
    configurations = report["runtime"].get("additional_configurations", {})
    if configurations:
        lines.append("Additional configurations:")
        lines.extend(f"- {name}: {entry.get('status', 'unknown')}" for name, entry in configurations.items())
    if report["collection_status"]["issues"]:
        lines.append("Issues:")
        lines.extend(f"- {issue['collector']}: {issue['message']}" for issue in report["collection_status"]["issues"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Intel hardware and OpenVINO environment advisor")
    parser.add_argument("--fixture", type=Path, help="Use a sanitized deterministic fixture")
    parser.add_argument("--validate-fixture", action="store_true", help="Validate a fixture without running discovery")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)
    try:
        profile = load_fixture(args.fixture) if args.fixture else collect_live()
    except ValueError:
        print("hardware-advisor: invalid or unsafe fixture", file=sys.stderr)
        return 2
    if args.validate_fixture:
        print("valid")
        return 0
    report = build_report(profile)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_text(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
