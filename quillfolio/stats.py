"""Summarize words, roles, and years in a local resume."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass

from quillfolio.errors import DateParseError, ResumeError
from quillfolio.textutil import as_str, string_list
from quillfolio.validate import parse_date

_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")


@dataclass(frozen=True)
class ResumeStats:
    words: int
    roles: int
    projects: int
    schools: int
    skills: int
    bullets: int
    years: float


def resume_stats(resume: dict, *, today: dt.date | None = None) -> ResumeStats:
    """Count words and entries, and sum the length of each role.

    ``years`` adds each experience entry from its start through its end.
    ``present`` and a missing end run through ``today``. Overlapping roles
    are both counted. Entries with a start date that cannot be read are skipped.
    """
    if not isinstance(resume, dict):
        raise ResumeError("resume must be a mapping")
    clock = today or dt.date.today()
    experience = _mappings(resume.get("experience"))
    projects = _mappings(resume.get("projects"))
    schools = _mappings(resume.get("education"))
    months = 0
    for role in experience:
        months += _role_months(role, clock)
    skill_count = 0
    for group in _mappings(resume.get("skills")):
        skill_count += len(string_list(group.get("items")))
    return ResumeStats(
        words=_word_count(resume),
        roles=len(experience),
        projects=len(projects),
        schools=len(schools),
        skills=skill_count,
        bullets=_bullet_count(experience) + _bullet_count(projects),
        years=round(months / 12, 1),
    )


def format_stats(stats: ResumeStats) -> str:
    lines = [
        f"words: {stats.words}",
        f"roles: {stats.roles}",
        f"projects: {stats.projects}",
        f"schools: {stats.schools}",
        f"skills: {stats.skills}",
        f"bullets: {stats.bullets}",
        f"years: {stats.years}",
    ]
    return "\n".join(lines) + "\n"


def _role_months(role: dict, today: dt.date) -> int:
    try:
        start = parse_date(role.get("start"), "start")
    except DateParseError:
        return 0
    if start.parts is None:
        return 0
    end_value = role.get("end")
    if end_value is None or (isinstance(end_value, str) and not end_value.strip()):
        end_parts = (today.year, today.month, today.day)
    else:
        try:
            end = parse_date(end_value, "end")
        except DateParseError:
            return 0
        if end.present or end.parts is None:
            end_parts = (today.year, today.month, today.day)
        else:
            end_parts = end.parts
    start_index = start.parts[0] * 12 + start.parts[1]
    end_index = end_parts[0] * 12 + end_parts[1]
    return max(0, end_index - start_index)


def _word_count(value: object) -> int:
    return len(_WORD_RE.findall(_text(value)))


def _text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_text(item) for item in value)
    return as_str(value)


def _bullet_count(entries: list[dict]) -> int:
    return sum(len(string_list(entry.get("highlights"))) for entry in entries)


def _mappings(entries: object) -> list[dict]:
    if not isinstance(entries, list):
        return []
    return [item for item in entries if isinstance(item, dict)]
