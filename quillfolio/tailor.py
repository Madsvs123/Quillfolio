"""Select resume sections that match a target role."""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field

from quillfolio.errors import ResumeError
from quillfolio.textutil import as_str

_STOP = frozenset(
    """
    a an the for and or of to in with on at by from as into over
    role position job using use our their it be is are was were
    """.split()
)
_TOKEN_RE = re.compile(r"[a-z0-9+#]+")
_KEEP_SHORT = {"c", "r"}


@dataclass
class TailorResult:
    """A tailored copy of a resume plus notes about what was kept."""

    resume: dict
    notes: list[str] = field(default_factory=list)
    kept_role_ids: list[str] = field(default_factory=list)
    dropped_role_ids: list[str] = field(default_factory=list)
    kept_project_ids: list[str] = field(default_factory=list)
    dropped_project_ids: list[str] = field(default_factory=list)


def tokenize(text: str) -> list[str]:
    """Break text into matchable words, dropping filler such as 'and' and 'the'."""
    if not isinstance(text, str):
        return []
    tokens: list[str] = []
    for token in _TOKEN_RE.findall(text.lower()):
        if token in _STOP:
            continue
        if len(token) == 1 and token not in _KEEP_SHORT:
            continue
        tokens.append(token)
    return tokens


def tailor_resume(
    resume: dict,
    target_role: str,
    keywords: list[str] | None = None,
    max_roles: int | None = None,
    max_projects: int | None = None,
) -> TailorResult:
    """Return a new resume that keeps experience and projects relevant to a role.

    Matching uses exact words from the target role and any extra keywords.
    Education stays in place. Skill groups with no matching word are omitted
    when at least one group matches; otherwise every skill group is kept.
    """
    if not isinstance(resume, dict):
        raise ResumeError("resume must be a mapping")
    target = as_str(target_role)
    if not target:
        raise ResumeError("target role is required")
    if max_roles is not None and max_roles < 1:
        raise ResumeError("max roles must be at least 1")
    if max_projects is not None and max_projects < 1:
        raise ResumeError("max projects must be at least 1")
    extra = keywords or []
    if any(not isinstance(word, str) for word in extra):
        raise ResumeError("keywords must be strings")

    targets: set[str] = set(tokenize(target))
    for word in extra:
        targets.update(tokenize(word))
    if not targets:
        raise ResumeError("target role did not contain any usable words")

    updated = copy.deepcopy(resume)
    meta = updated.get("meta")
    if not isinstance(meta, dict):
        raise ResumeError("meta must be a mapping")
    meta["tailored_for"] = target

    notes: list[str] = []
    roles, kept_role_ids, dropped_role_ids, role_notes = _select_entries(
        updated.get("experience", []),
        "experience",
        targets,
        max_roles,
    )
    projects, kept_project_ids, dropped_project_ids, project_notes = _select_entries(
        updated.get("projects", []),
        "projects",
        targets,
        max_projects,
    )
    notes.extend(role_notes)
    notes.extend(project_notes)

    if "experience" in resume or roles:
        updated["experience"] = roles
    if "projects" in resume or projects:
        updated["projects"] = projects

    if isinstance(updated.get("skills"), list):
        skills, skill_note = _select_skills(updated["skills"], targets)
        updated["skills"] = skills
        if skill_note:
            notes.append(skill_note)

    return TailorResult(
        resume=updated,
        notes=notes,
        kept_role_ids=kept_role_ids,
        dropped_role_ids=dropped_role_ids,
        kept_project_ids=kept_project_ids,
        dropped_project_ids=dropped_project_ids,
    )


def score_item(item: dict, targets: set[str]) -> int:
    """Score one role or project. Higher means a closer word overlap."""
    score = 0
    skills = item.get("skills") or []
    if isinstance(skills, list):
        for skill in skills:
            overlap = set(tokenize(as_str(skill))) & targets
            score += 5 * len(overlap)
    title = as_str(item.get("title") or item.get("name"))
    score += 3 * len(set(tokenize(title)) & targets)
    score += len(set(tokenize(as_str(item.get("company")))) & targets)
    highlight_tokens: set[str] = set()
    highlights = item.get("highlights") or []
    if isinstance(highlights, list):
        for highlight in highlights:
            highlight_tokens.update(tokenize(as_str(highlight)))
    score += min(4, len(highlight_tokens & targets))
    description_overlap = set(tokenize(as_str(item.get("description")))) & targets
    score += min(2, len(description_overlap))
    return score


def _select_entries(
    entries: object,
    section: str,
    targets: set[str],
    limit: int | None,
) -> tuple[list[dict], list[str], list[str], list[str]]:
    if entries is None:
        entries = []
    if not isinstance(entries, list):
        raise ResumeError(f"{section} must be a list")
    notes: list[str] = []
    ranked: list[tuple[int, int, dict]] = []
    for index, item in enumerate(entries):
        if not isinstance(item, dict):
            raise ResumeError(f"{section} entries must be mappings")
        ranked.append((score_item(item, targets), index, item))
    matched = [row for row in ranked if row[0] > 0]
    matched.sort(key=lambda row: (-row[0], row[1]))
    match_count = len(matched)
    if limit is not None and match_count > limit:
        notes.append(f"kept {limit} of {match_count} matching {section} entries")
        matched = matched[:limit]
    kept_ids = [_entry_id(row[2], row[1], section) for row in matched]
    kept_objects = {id(row[2]) for row in matched}
    dropped_ids = [
        _entry_id(row[2], row[1], section) for row in ranked if id(row[2]) not in kept_objects
    ]
    if entries and not matched:
        if section == "experience":
            notes.append("no experience entries matched the target role; that section is empty")
        elif section == "projects":
            notes.append("no project entries matched the target role; that section is empty")
        else:
            notes.append(f"no {section} entries matched the target role; that section is empty")
    return [row[2] for row in matched], kept_ids, dropped_ids, notes


def _select_skills(groups: list, targets: set[str]) -> tuple[list, str | None]:
    scored: list[tuple[int, int, dict]] = []
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            raise ResumeError("skill groups must be mappings")
        items = group.get("items") or []
        if not isinstance(items, list):
            items = []
        matched: list[str] = []
        rest: list[str] = []
        group_score = 2 * len(set(tokenize(as_str(group.get("group")))) & targets)
        for item in items:
            text = as_str(item)
            if not text:
                continue
            overlap = set(tokenize(text)) & targets
            if overlap:
                matched.append(text)
                group_score += 5 * len(overlap)
            else:
                rest.append(item if isinstance(item, str) else text)
        rewritten = dict(group)
        rewritten["items"] = matched + rest
        scored.append((group_score, index, rewritten))
    if not any(score > 0 for score, _, _ in scored):
        return groups, "no skill groups matched; kept every skill group"
    kept = [group for score, _, group in sorted(scored, key=lambda row: (-row[0], row[1])) if score > 0]
    return kept, None


def _entry_id(item: dict, index: int, section: str) -> str:
    ident = item.get("id")
    if isinstance(ident, str) and ident.strip():
        return ident.strip()
    return f"{section}-{index + 1}"
