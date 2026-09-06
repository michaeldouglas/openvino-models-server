---
name: intel-openvino-installer
description: Choose, install, and verify OpenVINO Runtime using the appropriate documented method for the user's operating system, ecosystem, version, and requested components.
---

# Intel OpenVINO Installer

Use this skill when a user asks to install, set up, repair, or verify OpenVINO
Runtime or an explicitly requested OpenVINO component.

The skill is standalone. It does not require `intel-docs-reader`,
`intel-hardware-advisor`, the harness, or any project file outside this skill.

## Workflow

1. The agent must invoke the bundled `scripts/openvino_installer.py` relative to this
   `SKILL.md`. Do not ask the user to locate the script or run it manually.
2. Start with plan mode and JSON output:

   ```text
   python scripts/openvino_installer.py --mode plan --format json
   ```

   Add the requested `--ecosystem`, `--method`, `--version`, `--target-dir`, or
   `--component` values when the user supplied them.
3. Inspect `collection_status`, `selection`, `plan`, and `issues`. Present the
   selected method, version, commands, prerequisites, warnings, and expected
   changes in plain language.
4. Ask for explicit confirmation immediately before applying any plan that
   changes the environment. A request to explain or plan installation is not
   confirmation to install.
5. After confirmation, run the same request with `--mode apply --confirm`.
   Never add `--confirm` before the user approves the displayed plan.
6. Verify the result with `--mode verify --format json` or use the verification
   returned by apply mode. Report the installed version, runtime import,
   visible devices, optional components, and unresolved driver prerequisites.
7. Keep installation success separate from model compatibility, precision,
   performance, and driver readiness. Those require additional evidence.

## Method routing

Read `references/installation-methods.md` only when selecting or explaining a
method. Prefer the user's existing ecosystem instead of silently replacing it
with Pip.

- Python: isolated environment with Pip.
- Windows system installation: versioned WinGet when the release identifier is
  explicit; archive fallback otherwise.
- Ubuntu/Debian-like Linux: APT when the repository/tooling is available.
- RHEL-like Linux: YUM; openSUSE: Zypper.
- macOS: Homebrew or the macOS archive.
- Conda, Node.js, vcpkg, Conan, Docker, Yocto, and source builds: use the
  matching profile and do not treat the host as a native installation.
- GenAI: install only when requested and verify it separately from core
  OpenVINO.

## Safety boundaries

- Plan mode is read-only. Apply mode is a mutating operation and requires the
  explicit confirmation gate above.
- Do not install GPU/NPU drivers, modify BIOS, source global setup scripts,
  change global environment variables, or run benchmarks in the default flow.
- Do not install the discontinued `openvino-dev` metapackage. Use `openvino`
  and requested optional extras instead.
- Do not expose tokens, credentials, personal paths, arbitrary environment
  dumps, or unredacted command output.
- If the system, architecture, package manager, repository, permission, version,
  or target context is unsupported or unknown, stop with a blocked or partial
  report instead of guessing.
- If OpenVINO installs successfully but no device is visible, report those as
  separate facts; do not claim the hardware is absent or incompatible.

## Output

Use the JSON report as the stable interface. A useful answer includes:

- detected context and requested ecosystem;
- selected method and why it was selected;
- exact version or version-resolution warning;
- confirmation status and actions that would run;
- installation and verification result;
- driver, device, model, precision, or performance limitations.

The `intel-docs-reader` skill may be used only if the user wants a deeper
versioned documentation interpretation. Its absence must never block this
installation workflow.
