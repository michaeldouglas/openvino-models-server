"""Search the official OpenVINO HTML archive, downloading it only on demand."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import urllib.error
import urllib.request
import zipfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any


ARCHIVE_URL = "https://github.com/michaeldouglas/intel-ai-skills/releases/download/openvino-docs-2026/2026.zip"
SOURCE_URL = "https://docs.openvino.ai/2026/"
MAX_ARCHIVE_BYTES = 2 * 1024 * 1024 * 1024
WORD_RE = re.compile(r"[a-z0-9][a-z0-9_+-]*", re.IGNORECASE)
GENERATED_PAGES = {"genindex.html", "search.html", "py-modindex.html"}


def default_cache_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    base = Path(local_app_data) if local_app_data else Path.home() / ".cache"
    return base / "intel-docs-reader" / "openvino-2026"


class _HtmlTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._skip_depth = 0
        self._in_title = False
        self._content_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered in {"main", "article"}:
            self._content_depth += 1
        elif lowered in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        elif lowered == "title" and self._skip_depth == 0:
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in {"main", "article"} and self._content_depth:
            self._content_depth -= 1
        elif lowered in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        elif lowered == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._skip_depth or (self._content_depth == 0 and not self._in_title):
            return
        value = re.sub(r"\s+", " ", data).strip()
        if not value:
            return
        if self._in_title:
            self.title_parts.append(value)
        self.text_parts.append(value)

    @property
    def title(self) -> str:
        return " ".join(self.title_parts).strip()

    @property
    def text(self) -> str:
        return " ".join(self.text_parts).strip()


def inspect_cache(snapshot: Path) -> tuple[str, list[str]]:
    if not snapshot.is_dir():
        return "missing", ["The local OpenVINO 2026 documentation cache is missing."]
    if not (snapshot / "index.html").is_file():
        return "invalid", ["The local documentation cache has no valid index.html."]
    if not any(snapshot.rglob("*.html")):
        return "invalid", ["The local documentation cache contains no HTML pages."]
    return "valid", []


def _download(url: str, target: Path) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "intel-docs-reader/1.0"})
    size = 0
    digest = hashlib.sha256()
    with urllib.request.urlopen(request, timeout=120) as response, target.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_ARCHIVE_BYTES:
                raise ValueError("The documentation archive exceeds the safety size limit.")
            output.write(chunk)
            digest.update(chunk)
    if size == 0:
        raise ValueError("The documentation archive is empty.")
    return digest.hexdigest()


def _extract_archive(archive_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive_path) as archive:
        total_size = 0
        for member in archive.infolist():
            member_path = PurePosixPath(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError("The documentation archive contains an unsafe path.")
            if not member.filename or member.filename.endswith("/"):
                continue
            if len(member_path.parts) > 1 and member_path.parts[0] == "2026":
                member_path = PurePosixPath(*member_path.parts[1:])
            if not member_path.parts:
                continue
            total_size += member.file_size
            if total_size > MAX_ARCHIVE_BYTES:
                raise ValueError("The extracted documentation exceeds the safety size limit.")
            target = destination.joinpath(*member_path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)


def ensure_snapshot(snapshot: Path, archive_url: str) -> bool:
    status, _ = inspect_cache(snapshot)
    if status == "valid":
        return False
    if snapshot.exists():
        raise ValueError(f"The existing documentation cache is {status}; refusing to overwrite it.")

    snapshot.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{snapshot.name}-", dir=snapshot.parent))
    archive_path = staging / "docs.zip"
    extracted = staging / "extracted"
    try:
        archive_sha256 = _download(archive_url, archive_path)
        _extract_archive(archive_path, extracted)
        if not (extracted / "index.html").is_file():
            raise ValueError("The archive does not contain the expected 2026/index.html page.")
        extracted.rename(snapshot)
        (snapshot / ".intel-docs-reader.json").write_text(
            json.dumps(
                {
                    "archive_url": archive_url,
                    "archive_sha256": archive_sha256,
                    "source_url": SOURCE_URL,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return True
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _parse_html(path: Path) -> tuple[str, str]:
    parser = _HtmlTextParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    return parser.title or path.stem.replace("-", " ").title(), parser.text


def _excerpt(text: str, tokens: list[str]) -> str:
    lowered = text.lower()
    positions = [lowered.find(token) for token in tokens if lowered.find(token) >= 0]
    start = max(0, (min(positions) if positions else 0) - 100)
    excerpt = text[start : start + 360].strip()
    return excerpt + ("…" if start + 360 < len(text) else "")


def search_docs(
    query: str,
    snapshot: Path | None = None,
    *,
    limit: int = 5,
    allow_download: bool = False,
    archive_url: str = ARCHIVE_URL,
) -> dict[str, Any]:
    snapshot = snapshot or default_cache_dir()
    downloaded = False
    status, limitations = inspect_cache(snapshot)
    if status != "valid" and allow_download:
        try:
            downloaded = ensure_snapshot(snapshot, archive_url)
            status, limitations = inspect_cache(snapshot)
        except (OSError, ValueError, urllib.error.URLError, zipfile.BadZipFile) as error:
            limitations = limitations + [f"Documentation download failed: {error.__class__.__name__}."]
    result: dict[str, Any] = {
        "cache_status": status,
        "cache_dir": str(snapshot),
        "downloaded": downloaded,
        "query": query,
        "matches": [],
        "limitations": limitations,
    }
    if status != "valid":
        return result
    tokens = [token.lower() for token in WORD_RE.findall(query) if len(token) > 1]
    if not tokens:
        result["limitations"].append("The query did not contain searchable terms.")
        return result

    candidates: list[tuple[int, Path, str, str]] = []
    for path in snapshot.rglob("*.html"):
        relative = path.relative_to(snapshot)
        if any(part.startswith("_") for part in relative.parts) or path.name.lower() in GENERATED_PAGES:
            continue
        try:
            title, text = _parse_html(path)
        except OSError:
            continue
        searchable = f"{title} {text}".lower()
        title_lower = title.lower()
        present_tokens = [token for token in tokens if token in searchable]
        score = sum(min(searchable.count(token), 8) for token in present_tokens)
        score += sum(12 for token in tokens if token in title_lower)
        if present_tokens and len(present_tokens) == len(tokens):
            score += 40
        if score:
            candidates.append((score, path, title, text))
    candidates.sort(key=lambda item: (-item[0], str(item[1])))
    for score, path, title, text in candidates[: max(1, min(limit, 20))]:
        relative = path.relative_to(snapshot).as_posix()
        result["matches"].append(
            {
                "title": title,
                "local_path": relative,
                "source_url": SOURCE_URL + relative,
                "score": score,
                "excerpt": _excerpt(text, tokens),
            }
        )
    if not result["matches"]:
        result["limitations"].append("No matching local page was found; uncaptured web pages were not consulted.")
    return result


def render_text(result: dict[str, Any]) -> str:
    lines = [
        f"OpenVINO docs cache: {result['cache_status']}",
        f"Cache directory: {result['cache_dir']}",
        f"Query: {result['query']}",
    ]
    if result.get("downloaded"):
        lines.append("The official archive was downloaded for this query.")
    if result["limitations"]:
        lines.append("Limitations:")
        lines.extend(f"- {item}" for item in result["limitations"])
    lines.append("Matches:")
    if not result["matches"]:
        lines.append("- No local matches.")
    for match in result["matches"]:
        lines.extend(
            [
                f"- {match['title']} [{match['local_path']}]",
                f"  Source: {match['source_url']}",
                f"  {match['excerpt']}",
            ]
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Search the on-demand OpenVINO 2026 documentation archive")
    parser.add_argument("--query", required=True)
    parser.add_argument("--docs-dir", type=Path, help="Use a specific extracted HTML cache")
    parser.add_argument("--archive-url", default=os.environ.get("INTEL_DOCS_ARCHIVE_URL", ARCHIVE_URL))
    parser.add_argument("--offline", action="store_true", help="Do not download a missing cache")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args(argv)
    result = search_docs(
        args.query,
        args.docs_dir or default_cache_dir(),
        limit=args.limit,
        allow_download=not args.offline,
        archive_url=args.archive_url,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_text(result), end="")
    return 0 if result["cache_status"] == "valid" else 2


if __name__ == "__main__":
    raise SystemExit(main())
