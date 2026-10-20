"""Save and restore resume versions in a folder beside the file."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from quillfolio.errors import ResumeError

_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,40}$")
_MANIFEST = "manifest.json"


@dataclass(frozen=True)
class Snapshot:
    number: str
    label: str
    filename: str


def snapshot_dir(resume_path: Path | str) -> Path:
    """Return the directory that holds snapshots for one resume file."""
    source = Path(resume_path)
    return source.resolve().parent / ".quillfolio-snapshots" / source.name


def take_snapshot(resume_path: Path | str, label: str, *, force: bool = False) -> Snapshot:
    """Copy the resume bytes into a labeled snapshot. The resume file is unchanged."""
    source = _existing_file(resume_path)
    cleaned = _label(label)
    root = snapshot_dir(source)
    root.mkdir(parents=True, exist_ok=True)
    records = _read_manifest(root)
    existing = next((record for record in records if record["label"] == cleaned), None)
    if existing is not None:
        if not force:
            raise ResumeError(f"snapshot {cleaned!r} already exists; pass --force to replace it")
        destination = root / existing["file"]
        destination.write_bytes(source.read_bytes())
        return Snapshot(existing["id"], cleaned, existing["file"])
    number = f"{_next_number(records):04d}"
    filename = f"{number}-{cleaned}{source.suffix.lower()}"
    (root / filename).write_bytes(source.read_bytes())
    records.append({"id": number, "label": cleaned, "file": filename})
    _write_manifest(root, records)
    return Snapshot(number, cleaned, filename)


def list_snapshots(resume_path: Path | str) -> list[Snapshot]:
    root = snapshot_dir(resume_path)
    if not root.is_dir():
        return []
    return [Snapshot(record["id"], record["label"], record["file"]) for record in _read_manifest(root)]


def format_snapshots(snapshots: list[Snapshot]) -> str:
    if not snapshots:
        return "snapshots: (none)\n"
    lines = [f"{item.number}  {item.label}  {item.filename}" for item in snapshots]
    return "\n".join(lines) + "\n"


def restore_snapshot(
    resume_path: Path | str,
    *,
    label: str | None = None,
    number: str | None = None,
) -> Snapshot:
    """Replace the resume file with a snapshot stored beside it."""
    if (label is None) == (number is None):
        raise ResumeError("pass a snapshot label or id")
    source = Path(resume_path)
    root = snapshot_dir(source)
    if not root.is_dir():
        raise ResumeError(f"no snapshots for {source}")
    records = _read_manifest(root)
    if label is not None:
        cleaned = _label(label)
        matches = [record for record in records if record["label"] == cleaned]
        if not matches:
            raise ResumeError(f"no snapshot labeled {cleaned!r}")
    else:
        ident = _number(number or "")
        matches = [record for record in records if record["id"] == ident]
        if not matches:
            raise ResumeError(f"no snapshot with id {ident}")
    record = matches[0]
    stored = root / record["file"]
    if not stored.is_file():
        raise ResumeError(f"snapshot file is missing: {stored.name}")
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(stored.read_bytes())
    return Snapshot(record["id"], record["label"], record["file"])


def _existing_file(resume_path: Path | str) -> Path:
    source = Path(resume_path)
    if not source.is_file():
        raise ResumeError(f"file not found: {source}")
    return source


def _label(value: str) -> str:
    if not isinstance(value, str) or not _LABEL_RE.fullmatch(value.strip()):
        raise ResumeError("label must use letters, numbers, hyphens, or underscores")
    return value.strip()


def _number(value: str) -> str:
    text = value.strip()
    if not text.isdigit():
        raise ResumeError("snapshot id must be a number")
    number = int(text)
    if not 1 <= number <= 9999:
        raise ResumeError("snapshot id must be from 1 to 9999")
    return f"{number:04d}"


def _next_number(records: list[dict]) -> int:
    highest = 0
    for record in records:
        highest = max(highest, int(record["id"]))
    if highest >= 9999:
        raise ResumeError("snapshot id space is full")
    return highest + 1


def _read_manifest(root: Path) -> list[dict]:
    path = root / _MANIFEST
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ResumeError(f"snapshot manifest is invalid: {path}") from exc
    if not isinstance(data, list):
        raise ResumeError(f"snapshot manifest is invalid: {path}")
    records: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            raise ResumeError(f"snapshot manifest is invalid: {path}")
        ident = item.get("id")
        label = item.get("label")
        filename = item.get("file")
        if not all(isinstance(value, str) and value for value in (ident, label, filename)):
            raise ResumeError(f"snapshot manifest is invalid: {path}")
        if Path(filename).name != filename:
            raise ResumeError(f"snapshot manifest is invalid: {path}")
        records.append({"id": ident, "label": label, "file": filename})
    return records


def _write_manifest(root: Path, records: list[dict]) -> None:
    path = root / _MANIFEST
    path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
