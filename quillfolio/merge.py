"""Merge two local resume files into one mapping."""

from __future__ import annotations

import copy

from quillfolio.errors import ResumeError
from quillfolio.textutil import as_str

_ENTRY_SECTIONS = ("experience", "projects", "education")


def merge_resumes(left: dict, right: dict) -> tuple[dict, list[str]]:
    """Combine two resumes. The left file wins when both set the same meta field or id.

    Skill categories are united by name. Items already present in a category are kept once.
    """
    if not isinstance(left, dict) or not isinstance(right, dict):
        raise ResumeError("resume must be a mapping")
    notes: list[str] = []
    merged: dict = {}
    merged["meta"] = _merge_meta(left.get("meta"), right.get("meta"), notes)
    for section in _ENTRY_SECTIONS:
        merged[section] = _merge_entries(section, left.get(section), right.get(section), notes)
    merged["skills"] = _merge_skills(left.get("skills"), right.get("skills"), notes)
    for key, value in left.items():
        if key not in merged:
            merged[key] = copy.deepcopy(value)
    for key, value in right.items():
        if key not in merged:
            merged[key] = copy.deepcopy(value)
            notes.append(f"added {key} from the second file")
    return merged, notes


def _merge_meta(left: object, right: object, notes: list[str]) -> dict:
    if not isinstance(left, dict) and not isinstance(right, dict):
        return {}
    if not isinstance(left, dict):
        notes.append("meta came from the second file")
        return copy.deepcopy(right) if isinstance(right, dict) else {}
    merged = copy.deepcopy(left)
    if isinstance(right, dict):
        for key, value in right.items():
            if key not in merged:
                merged[key] = copy.deepcopy(value)
                notes.append(f"filled meta.{key} from the second file")
    return merged


def _merge_entries(section: str, left: object, right: object, notes: list[str]) -> list:
    entries: list = []
    seen: set[str] = set()
    for source_name, source in (("first", left), ("second", right)):
        if source is None:
            continue
        if not isinstance(source, list):
            raise ResumeError(f"{section} must be a list")
        for entry in source:
            if not isinstance(entry, dict):
                if source_name == "first":
                    entries.append(copy.deepcopy(entry))
                continue
            ident = as_str(entry.get("id"))
            if ident and ident in seen:
                notes.append(f"skipped {section} {ident} from the second file; id already present")
                continue
            if ident:
                seen.add(ident)
            elif source_name == "second":
                notes.append(f"appended a {section} entry that has no id")
            entries.append(copy.deepcopy(entry))
    return entries


def _merge_skills(left: object, right: object, notes: list[str]) -> list:
    if left is None and right is None:
        return []
    if left is not None and not isinstance(left, list):
        raise ResumeError("skills must be a list of groups")
    if right is not None and not isinstance(right, list):
        raise ResumeError("skills must be a list of groups")
    groups: list[dict] = []
    index: dict[str, dict] = {}
    for source_name, source in (("first", left), ("second", right)):
        for group in source or []:
            if not isinstance(group, dict):
                continue
            label = as_str(group.get("group"))
            key = label.casefold()
            items = group.get("items")
            if not isinstance(items, list):
                items = []
            if key and key in index:
                target = index[key]
                added = _union_items(target, items)
                if source_name == "second" and added:
                    notes.append(f"merged {added} skill(s) into {target.get('group')}")
                continue
            copied = {"group": label or "Skills", "items": []}
            _union_items(copied, items)
            groups.append(copied)
            if key:
                index[key] = copied
            elif source_name == "second":
                notes.append("added a skill group from the second file")
    return groups


def _union_items(group: dict, items: list) -> int:
    existing = group["items"]
    seen = {as_str(item).casefold() for item in existing if as_str(item)}
    added = 0
    for item in items:
        text = as_str(item)
        if not text:
            continue
        token = text.casefold()
        if token in seen:
            continue
        seen.add(token)
        existing.append(text)
        added += 1
    return added
