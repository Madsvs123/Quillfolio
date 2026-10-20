"""Small text helpers shared by loading, checking, and rendering."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_SAFE_SCHEMES = {"http", "https", "mailto"}


def as_str(value: object) -> str:
    """Return stripped text, or an empty string when the value is not text."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, bool):
        return ""
    if isinstance(value, int):
        return str(value)
    return ""


def string_list(value: object) -> list[str]:
    """Return the non-empty strings in a list, skipping anything else."""
    if not isinstance(value, list):
        return []
    cleaned: list[str] = []
    for item in value:
        text = as_str(item)
        if text:
            cleaned.append(text)
    return cleaned


def is_email(value: str) -> bool:
    return bool(_EMAIL_RE.fullmatch(value))


def safe_href(value: object) -> str | None:
    """Return a URL that is safe to place in an href, or None."""
    candidate = as_str(value)
    if not candidate:
        return None
    if any(ord(char) < 32 or char in "\"'<>\\" or char.isspace() for char in candidate):
        return None
    parts = urlsplit(candidate)
    scheme = parts.scheme.lower()
    if scheme not in _SAFE_SCHEMES:
        return None
    if scheme in {"http", "https"} and not parts.netloc:
        return None
    if scheme == "mailto" and "@" not in parts.path:
        return None
    return candidate


def slugify(value: object) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", as_str(value).lower()).strip("-")
    return slug[:48]


def plain(value: object) -> str:
    """Collapse a value to a single line for diffs and labels."""
    if value is None or isinstance(value, bool):
        if isinstance(value, bool):
            return "true" if value else "false"
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    if isinstance(value, list):
        return ", ".join(item for item in (plain(entry) for entry in value) if item)
    if isinstance(value, dict):
        parts = [f"{key}={plain(item)}" for key, item in value.items()]
        return "; ".join(parts)
    return " ".join(str(value).split())
