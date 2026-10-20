"""Read and extend skill groups on a local resume."""

from __future__ import annotations

import copy

from quillfolio.errors import ResumeError
from quillfolio.textutil import as_str, string_list


def grouped_skills(resume: dict) -> list[tuple[str, list[str]]]:
    """Return ``(category, items)`` pairs in file order."""
    if not isinstance(resume, dict):
        raise ResumeError("resume must be a mapping")
    skills = resume.get("skills")
    if skills is None:
        return []
    if not isinstance(skills, list):
        raise ResumeError("skills must be a list of groups")
    groups: list[tuple[str, list[str]]] = []
    for group in skills:
        if not isinstance(group, dict):
            continue
        label = as_str(group.get("group")) or "Skills"
        groups.append((label, string_list(group.get("items"))))
    return groups


def format_skills(resume: dict) -> str:
    """Render skill categories as plain text."""
    groups = grouped_skills(resume)
    if not groups:
        return "skills: (none)\n"
    lines: list[str] = []
    for label, items in groups:
        lines.append(label)
        if items:
            lines.extend(f"- {item}" for item in items)
        else:
            lines.append("- (empty)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def add_skill(resume: dict, group: str, item: str) -> dict:
    """Return a copy with ``item`` added to the named skill category.

    The category is matched without regard to case. A new category is
    appended when none of the existing groups use that name.
    """
    if not isinstance(resume, dict):
        raise ResumeError("resume must be a mapping")
    label = as_str(group)
    skill = as_str(item)
    if not label:
        raise ResumeError("group is required")
    if not skill:
        raise ResumeError("skill is required")
    updated = copy.deepcopy(resume)
    skills = updated.get("skills")
    if skills is None:
        skills = []
        updated["skills"] = skills
    if not isinstance(skills, list):
        raise ResumeError("skills must be a list of groups")

    target: dict | None = None
    for existing in skills:
        if isinstance(existing, dict) and as_str(existing.get("group")).casefold() == label.casefold():
            target = existing
            break
    if target is None:
        target = {"group": label, "items": []}
        skills.append(target)
    items = target.get("items")
    if items is None:
        items = []
        target["items"] = items
    if not isinstance(items, list):
        raise ResumeError("skill items must be a list")
    if any(as_str(current).casefold() == skill.casefold() for current in items):
        raise ResumeError(f"{skill!r} is already in {as_str(target.get('group')) or label}")
    items.append(skill)
    return updated
