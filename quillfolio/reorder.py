"""Reorder resume sections or the entries inside one section."""

from __future__ import annotations

import copy

from quillfolio.errors import ResumeError

SECTIONS = ("meta", "experience", "projects", "education", "skills")
ENTRY_SECTIONS = ("experience", "projects", "education")


def reorder_sections(resume: dict, order: list[str]) -> dict:
    """Return a copy whose named sections follow ``order``.

    Sections you do not name stay in their usual order after the ones you name.
    Extra keys that are not resume sections keep their relative order at the end.
    """
    updated = _copy(resume)
    names = _unique(order, "section")
    unknown = [name for name in names if name not in SECTIONS]
    if unknown:
        known = ", ".join(SECTIONS)
        raise ResumeError(f"unknown section {unknown[0]!r}. Choose one of: {known}")
    tail = [name for name in SECTIONS if name in updated and name not in names]
    extras = [key for key in updated if key not in SECTIONS]
    rebuilt: dict = {}
    for key in [*names, *tail, *extras]:
        if key in updated:
            rebuilt[key] = updated[key]
    return rebuilt


def reorder_entries(resume: dict, section: str, ids: list[str]) -> dict:
    """Return a copy with entries in ``section`` arranged by id.

    Ids you do not name stay after the ones you name, in their previous order.
    """
    updated = _copy(resume)
    if section not in ENTRY_SECTIONS:
        known = ", ".join(ENTRY_SECTIONS)
        raise ResumeError(f"cannot reorder entries in {section!r}. Choose one of: {known}")
    wanted = _unique(ids, "id")
    entries = updated.get(section)
    if entries is None:
        entries = []
    if not isinstance(entries, list):
        raise ResumeError(f"{section} must be a list")
    by_id: dict[str, dict] = {}
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("id"), str) and entry["id"].strip():
            by_id[entry["id"].strip()] = entry
    missing = [entry_id for entry_id in wanted if entry_id not in by_id]
    if missing:
        raise ResumeError(f"unknown id {missing[0]!r} in {section}")
    used = set(wanted)
    ordered = [by_id[entry_id] for entry_id in wanted]
    for entry in entries:
        ident = ""
        if isinstance(entry, dict) and isinstance(entry.get("id"), str):
            ident = entry["id"].strip()
        if ident not in used:
            ordered.append(entry)
    updated[section] = ordered
    return updated


def _copy(resume: dict) -> dict:
    if not isinstance(resume, dict):
        raise ResumeError("resume must be a mapping")
    return copy.deepcopy(resume)


def _unique(values: list[str], label: str) -> list[str]:
    if not values:
        raise ResumeError(f"pass at least one {label}")
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ResumeError(f"{label} must be non-empty text")
        text = value.strip()
        if text in seen:
            raise ResumeError(f"repeated {label} {text!r}")
        seen.add(text)
        cleaned.append(text)
    return cleaned
