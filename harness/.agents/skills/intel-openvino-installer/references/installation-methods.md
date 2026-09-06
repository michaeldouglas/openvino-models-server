# OpenVINO Installation Methods

This is a compact routing reference for the OpenVINO 2026 documentation. The
installer uses it to select a method; it does not replace the official
versioned instructions.

| Method | Best fit | Important boundary |
|--------|----------|-------------------|
| Pip | Python applications | Prefer an isolated virtual environment |
| Archive | Full C/C++ and Python toolkit | Requires exact OS, architecture and release artifact |
| APT | Ubuntu/Debian-like Linux | Intel repository and key setup may be required |
| YUM | RHEL-like Linux | Intel repository must be configured |
| Zypper | openSUSE | Package names include development/sample packages in the documented path |
| Conda Forge | Conda-managed Python | Preserve the existing Conda environment |
| Homebrew | macOS | The supported macOS path is CPU-focused |
| WinGet | Windows system package | Use an explicit versioned package identifier |
| Docker | Linux/container workflows | Select a documented registry image; do not mutate the host as native install |
| npm | Node.js projects | Installs the JavaScript API package |
| vcpkg | C/C++ projects | Supports C/C++ integration and project-level CMake configuration |
| Conan | C/C++ projects | The documented profile does not offer NPU inference |
| Yocto | Embedded images | Requires a project-specific OpenEmbedded build tree |
| Source | Advanced custom builds | Planning only unless the user supplies a build scope |

## Version policy

The OpenVINO 2026 documentation identifies 2026.3 as non-LTS, with 2026.3.1
development and 2025.4.1 maintenance lines in the version overview. Prefer a
maintenance release for production-oriented requests, but honor an exact
version requested by the user and warn when its support status is not clear.

## Optional components

- Core Python integrations use `openvino` and requested extras such as
  `openvino[onnx]` or `openvino[tensorflow2]`.
- OpenVINO GenAI uses its own PyPI, npm, or archive profile and must be checked
  separately.
- GPU and NPU drivers, OpenCL, Level Zero, kernel and WSL setup are additional
  configuration concerns, not proof of a successful runtime installation.

## Official documentation

- https://docs.openvino.ai/2026.3/get-started/install-openvino/install-openvino-pip.html
- https://docs.openvino.ai/2026.3/get-started/install-openvino/install-openvino-winget.html
- https://docs.openvino.ai/2026.3/get-started/install-openvino/install-openvino-apt.html
- https://docs.openvino.ai/2026.3/get-started/install-openvino/install-openvino-yum.html
- https://docs.openvino.ai/2026.3/get-started/install-openvino/install-openvino-zypper.html
- https://docs.openvino.ai/2026.3/get-started/install-openvino/install-openvino-conda.html
- https://docs.openvino.ai/2026.3/get-started/install-openvino/install-openvino-docker-linux.html
- https://docs.openvino.ai/2026.3/get-started/install-openvino/install-openvino-genai.html
