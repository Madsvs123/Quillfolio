"""Compare two resume mappings and describe what changed."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from quillfolio.textutil import plain, string_list

_META_FIELDS = (
    "name",
    "headline",
    "email",
    "phone",
    "location",
    "website",
    "summary",
    "tailored_for",
)
_SCALARS = {
    "experience": ("company", "title", "location", "start", "end"),
    "project": ("name", "url", "description"),
    "education": ("school", "degree", "start", "end", "details"),
    "skill": ("group",),
}
_SEQUENCES = {
    "experience": ("highlights", "skills"),
    "project": ("highlights", "skills"),
    "education": (),
    "skill": ("items",),
}


@dataclass(frozen=True)
class DiffEntry:
    kind: str
    path: str
    before: str | None = None
    after: str | None = None


def diff_resumes(left: dict, right: dict) -> list[DiffEntry]:
    """Return structural changes from left to right."""
    if not isinstance(left, dict) or not isinstance(right, dict):
        raise TypeError("both resumes must be mappings")
    entries: list[DiffEntry] = []
    _diff_meta(left, right, entries)
    _diff_section(left, right, "experience", "experience", entries)
    _diff_section(left, right, "projects", "project", entries)
    _diff_section(left, right, "education", "education", entries)
    _diff_section(left, right, "skills", "skill", entries)
    return entries


def format_diff(entries: list[DiffEntry]) -> str:
    """Render diff entries as plain text. Identical resumes produce one line."""
    if not entries:
        return "No differences.\n"
    noun = "difference" if len(entries) == 1 else "differences"
    lines = [f"Quillfolio diff: {len(entries)} {noun}"]
    for entry in entries:
        if entry.kind == "changed":
            lines.append(f"changed {entry.path}")
            lines.append(f"  - {entry.before or ''}")
            lines.append(f"  + {entry.after or ''}")
        elif entry.kind == "added":
            lines.append(f"added {entry.path}")
            if entry.after:
                lines.append(f"  + {entry.after}")
        elif entry.kind == "removed":
            lines.append(f"removed {entry.path}")
            if entry.before:
                lines.append(f"  - {entry.before}")
    return "\n".join(lines) + "\n"


def _diff_meta(left: dict, right: dict, entries: list[DiffEntry]) -> None:
    left_meta = left.get("meta")
    right_meta = right.get("meta")
    if not isinstance(left_meta, dict) or not isinstance(right_meta, dict):
        if plain(left_meta) != plain(right_meta):
            entries.append(DiffEntry("changed", "meta", before=plain(left_meta), after=plain(right_meta)))
        return
    fields = list(_META_FIELDS)
    extras = sorted((set(left_meta) | set(right_meta)) - set(_META_FIELDS))
    for name in fields + extras:
        before = plain(left_meta.get(name))
        after = plain(right_meta.get(name))
        if before != after:
            entries.append(DiffEntry("changed", f"meta.{name}", before=before, after=after))


def _diff_section(
    left: dict,
    right: dict,
    field: str,
    kind: str,
    entries: list[DiffEntry],
) -> None:
    left_items = _coerce_section(left, field)
    right_items = _coerce_section(right, field)
    if left_items is None or right_items is None:
        if plain(left.get(field)) != plain(right.get(field)):
            entries.append(
                DiffEntry("changed", field, before=plain(left.get(field)), after=plain(right.get(field)))
            )
        return
    left_aligned = _align(left_items, kind)
    right_aligned = _align(right_items, kind)
    left_map = dict(left_aligned)
    right_map = dict(right_aligned)
    for key, item in left_aligned:
        if key not in right_map:
            entries.append(DiffEntry("removed", f"{field}[{key}]", before=_describe(kind, item)))
        else:
            _diff_item(field, kind, key, item, right_map[key], entries)
    for key, item in right_aligned:
        if key not in left_map:
            entries.append(DiffEntry("added", f"{field}[{key}]", after=_describe(kind, item)))


def _diff_item(
    field: str,
    kind: str,
    key: str,
    left_item: dict,
    right_item: dict,
    entries: list[DiffEntry],
) -> None:
    prefix = f"{field}[{key}]"
    for name in _SCALARS[kind]:
        before = plain(left_item.get(name))
        after = plain(right_item.get(name))
        if before != after:
            entries.append(DiffEntry("changed", f"{prefix}.{name}", before=before, after=after))
    for name in _SEQUENCES[kind]:
        _diff_sequence(f"{prefix}.{name}", _as_lines(left_item.get(name)), _as_lines(right_item.get(name)), entries)


def _diff_sequence(path: str, before: list[str], after: list[str], entries: list[DiffEntry]) -> None:
    if before == after:
        return
    removed, added = _multiset_changes(before, after)
    if not removed and not added:
        entries.append(DiffEntry("changed", path, before=" | ".join(before), after=" | ".join(after)))
        return
    for line in removed:
        entries.append(DiffEntry("removed", path, before=line))
    for line in added:
        entries.append(DiffEntry("added", path, after=line))


def _multiset_changes(before: list[str], after: list[str]) -> tuple[list[str], list[str]]:
    before_counts = Counter(before)
    after_counts = Counter(after)
    removed: list[str] = []
    removed_seen: Counter[str] = Counter()
    for line in before:
        if removed_seen[line] < before_counts[line] - after_counts[line]:
            removed.append(line)
            removed_seen[line] += 1
    added: list[str] = []
    added_seen: Counter[str] = Counter()
    for line in after:
        if added_seen[line] < after_counts[line] - before_counts[line]:
            added.append(line)
            added_seen[line] += 1
    return removed, added


def _coerce_section(resume: dict, field: str) -> list | None:
    if field not in resume or resume[field] is None:
        return []
    value = resume[field]
    if isinstance(value, list):
        return value
    return None


def _align(items: list, kind: str) -> list[tuple[str, dict]]:
    counts: dict[str, int] = {}
    aligned: list[tuple[str, dict]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        base = _stable_key(item, kind)
        counts[base] = counts.get(base, 0) + 1
        key = base if counts[base] == 1 else f"{base}#{counts[base]}"
        aligned.append((key, item))
    return aligned


def _stable_key(item: dict, kind: str) -> str:
    ident = item.get("id")
    if isinstance(ident, str) and ident.strip():
        return ident.strip()
    if kind == "experience":
        parts = [plain(item.get("company")), plain(item.get("title")), plain(item.get("start"))]
    elif kind == "project":
        parts = [plain(item.get("name"))]
    elif kind == "education":
        parts = [plain(item.get("school")), plain(item.get("degree"))]
    elif kind == "skill":
        parts = [plain(item.get("group"))]
    else:
        parts = []
    base = "|".join(part for part in parts if part)
    return base or kind


def _describe(kind: str, item: dict) -> str:
    if kind == "experience":
        title = plain(item.get("title")) or "Untitled role"
        company = plain(item.get("company"))
        return f"{title} @ {company}" if company else title
    if kind == "project":
        return plain(item.get("name")) or "Untitled project"
    if kind == "education":
        degree = plain(item.get("degree"))
        school = plain(item.get("school"))
        if degree and school:
            return f"{degree} @ {school}"
        return degree or school or "Education"
    if kind == "skill":
        name = plain(item.get("group")) or "Skills"
        items = ", ".join(string_list(item.get("items")))
        return f"{name}: {items}" if items else name
    return kind


def _as_lines(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return string_list(value)
    text = plain(value)
    return [text] if text else []
