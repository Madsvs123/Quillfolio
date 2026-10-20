"""Read and write a resume kept in local YAML or JSON."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from quillfolio.errors import ResumeError

MAX_RESUME_BYTES = 2_000_000
_YAML_SUFFIXES = {".yaml", ".yml"}
_DATE_RE = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")
_NUMBER_RE = re.compile(r"^[+-]?(?:\d+|\d+\.\d+)(?:[eE][+-]?\d+)?$")
_QUOTE_WORDS = {
    "true",
    "false",
    "null",
    "yes",
    "no",
    "on",
    "off",
    "y",
    "n",
    "~",
}
_SPECIAL_START = set("!&*?{}[],|>%@`'\\\":-#")


class ResumeDumper(yaml.SafeDumper):
    """Dump resume mappings without anchors, quoting values YAML would reinterpret."""

    def ignore_aliases(self, data: object) -> bool:
        return True


def _should_quote(value: str) -> bool:
    if value == "" or value != value.strip():
        return True
    if value.lower() in _QUOTE_WORDS:
        return True
    if _NUMBER_RE.fullmatch(value) or _DATE_RE.fullmatch(value):
        return True
    if value[0] in _SPECIAL_START or value[0].isdigit():
        return True
    if any(char in value for char in ":#{}[]&*!|>"):
        return True
    return False


def _represent_str(dumper: yaml.SafeDumper, data: str):
    if "\n" in data and data.strip() == data:
        style = "|"
    elif _should_quote(data):
        style = '"'
    else:
        style = None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


ResumeDumper.add_representer(str, _represent_str)


def dump_yaml(resume: dict) -> str:
    text = yaml.dump(
        resume,
        Dumper=ResumeDumper,
        sort_keys=False,
        allow_unicode=True,
        width=88,
        default_flow_style=False,
    )
    if not text.endswith("\n"):
        text += "\n"
    return text


def load_resume(path: Path | str) -> dict:
    """Load a resume mapping from a UTF-8 YAML or JSON file."""
    source = Path(path)
    if not source.is_file():
        raise ResumeError(f"file not found: {source}")
    size = source.stat().st_size
    if size > MAX_RESUME_BYTES:
        raise ResumeError(f"resume file is larger than {MAX_RESUME_BYTES} bytes: {source}")
    try:
        raw = source.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ResumeError(f"resume file must be UTF-8: {source}") from exc

    suffix = source.suffix.lower()
    try:
        if suffix == ".json":
            data = json.loads(raw)
        elif suffix in _YAML_SUFFIXES:
            data = yaml.safe_load(raw)
        else:
            raise ResumeError("resume file must end in .yaml, .yml, or .json")
    except json.JSONDecodeError as exc:
        raise ResumeError(f"invalid JSON in {source}: {exc.msg}") from exc
    except yaml.YAMLError as exc:
        raise ResumeError(f"invalid YAML in {source}: {exc}") from exc

    if data is None:
        raise ResumeError(f"resume file is empty: {source}")
    if not isinstance(data, dict):
        raise ResumeError("resume file must contain a mapping at the top level")
    return data


def save_resume(path: Path | str, resume: dict) -> None:
    """Write a resume mapping as YAML or JSON, based on the file suffix."""
    if not isinstance(resume, dict):
        raise ResumeError("resume must be a mapping")
    destination = Path(path)
    suffix = destination.suffix.lower()
    if suffix == ".json":
        text = json.dumps(resume, indent=2, ensure_ascii=False) + "\n"
    elif suffix in _YAML_SUFFIXES:
        text = dump_yaml(resume)
    else:
        raise ResumeError("can only write .yaml, .yml, or .json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def dump_text(resume: dict, path_for_format: Path | str) -> str:
    """Serialize a resume using the format implied by a path suffix."""
    if Path(path_for_format).suffix.lower() == ".json":
        return json.dumps(resume, indent=2, ensure_ascii=False) + "\n"
    return dump_yaml(resume)
