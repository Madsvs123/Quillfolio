"""Read a local quillfolio.yaml for the default theme and name."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from quillfolio.errors import ResumeError
from quillfolio.html_render import normalize_theme

_FIELDS = {"theme", "name"}
_CONFIG_NAME = "quillfolio.yaml"


@dataclass(frozen=True)
class Config:
    path: Path | None
    theme: str
    name: str | None


def load_config(resume_path: Path | str | None = None) -> Config:
    """Load quillfolio.yaml from the working directory, then from beside the resume.

    The working directory wins when both places have a file. A missing file
    means theme ``atelier`` and no default name.
    """
    path = _find(resume_path)
    if path is None:
        return Config(None, "atelier", None)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ResumeError(f"invalid config file: {path}") from exc
    except UnicodeDecodeError as exc:
        raise ResumeError(f"config file must be UTF-8: {path}") from exc
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ResumeError("config file must be a mapping")
    unknown = [key for key in data if key not in _FIELDS]
    if unknown:
        raise ResumeError(f"unknown config field {unknown[0]!r}")
    theme_value = data.get("theme", "atelier")
    if not isinstance(theme_value, str) or not theme_value.strip():
        raise ResumeError("config theme must be text")
    name_value = data.get("name")
    name: str | None
    if name_value is None:
        name = None
    elif isinstance(name_value, str) and name_value.strip():
        name = name_value.strip()
    else:
        raise ResumeError("config name must be non-empty text")
    return Config(path, normalize_theme(theme_value), name)


def format_config(config: Config) -> str:
    location = str(config.path) if config.path is not None else "(none)"
    name = config.name if config.name else "(unset)"
    return f"file: {location}\ntheme: {config.theme}\nname: {name}\n"


def _find(resume_path: Path | str | None) -> Path | None:
    candidates = [Path.cwd() / _CONFIG_NAME]
    if resume_path is not None:
        beside = Path(resume_path).resolve().parent / _CONFIG_NAME
        if beside.resolve() != candidates[0].resolve():
            candidates.append(beside)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None
