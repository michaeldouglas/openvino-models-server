---
name: intel-docs-reader
description: Search and cite the on-demand local OpenVINO 2026 documentation archive for API, device, setup, configuration, and documented limitation questions.
---

# Intel Docs Reader

Use this skill when a question requires authoritative OpenVINO documentation.
The skill searches a local cache of the official HTML archive and reports the
source page for every useful result.

## Behavior

- The skill does not download anything when it is installed.
- On the first query, if the local cache is missing, the bundled reader asks
  the runtime to download the configured official archive and extracts it into
  the user's local cache, outside the installed skill and repository.
- Later queries reuse that cache instead of downloading again.
- Use `--offline` when network access is not allowed or a caller wants to use
  only an existing cache.
- If the archive is missing, invalid, or incomplete, disclose that limitation
  instead of presenting uncaptured web content as documentation.

## Use

When this skill is activated, invoke the bundled
`scripts/read_openvino_docs.py` yourself with the user's technical question.
Resolve that path relative to the directory containing this `SKILL.md`; do not
assume the user's current working directory. Use `--offline` when only the
existing cache may be used.

Do not ask the user to change directories, locate the script, or run the
reader manually. The skill owns the lookup, source extraction, and citation.

The archive source can be overridden with `--archive-url` or the
`INTEL_DOCS_ARCHIVE_URL` environment variable. The default points to the
repository's published OpenVINO documentation release asset. A release asset
is intentionally separate from this skill package, so installing the skill
does not download the large documentation archive.

## Evidence boundaries

Keep documented claims separate from local hardware detection, measurements,
estimates, and inferences. Preserve the archive version and source URL in the
answer. Do not extend a page's claim beyond its documented OpenVINO release or
hardware scope.
