"""Order experience and education by start date."""

from __future__ import annotations

import copy

from quillfolio.errors import DateParseError, ResumeError
from quillfolio.validate import parse_date


def sort_by_date(resume: dict, *, descending: bool = True) -> dict:
    """Return a copy with experience and education ordered by start date.

    Entries whose start date cannot be read stay at the end, in their
    previous order. The default puts the newest start date first.
    """
    if not isinstance(resume, dict):
        raise ResumeError("resume must be a mapping")
    updated = copy.deepcopy(resume)
    for section in ("experience", "education"):
        entries = updated.get(section)
        if entries is None:
            continue
        if not isinstance(entries, list):
            raise ResumeError(f"{section} must be a list")
        dated: list[tuple[tuple[int, int, int], int, object]] = []
        undated: list[object] = []
        for index, entry in enumerate(entries):
            key = _start_key(entry)
            if key is None:
                undated.append(entry)
            else:
                dated.append((key, index, entry))
        dated.sort(key=lambda item: (item[0], item[1]), reverse=descending)
        updated[section] = [item[2] for item in dated] + undated
    return updated


def _start_key(entry: object) -> tuple[int, int, int] | None:
    if not isinstance(entry, dict):
        return None
    if "start" not in entry:
        return None
    try:
        parsed = parse_date(entry.get("start"), "start")
    except DateParseError:
        return None
    return parsed.parts
