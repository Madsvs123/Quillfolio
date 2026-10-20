"""Render a resume as plain text for a terminal or a text editor."""

from __future__ import annotations

from quillfolio.errors import ResumeError
from quillfolio.textutil import as_str, string_list


def render_plain(resume: dict, width: int = 72) -> str:
    """Render the resume as wrapped plain text. No markup, no remote assets."""
    if not isinstance(resume, dict):
        raise ResumeError("resume must be a mapping")
    if isinstance(width, bool) or not isinstance(width, int) or not 40 <= width <= 120:
        raise ResumeError("width must be an integer from 40 to 120")
    meta = resume.get("meta") if isinstance(resume.get("meta"), dict) else {}
    lines: list[str] = []
    name = as_str(meta.get("name")) or "Resume"
    lines.append(name)
    lines.append("-" * min(len(name), width))
    headline = as_str(meta.get("headline"))
    if headline:
        lines.extend(_wrap(headline, width))
    contact = _contact(meta)
    if contact:
        lines.extend(_wrap(" | ".join(contact), width))
    tailored = as_str(meta.get("tailored_for"))
    if tailored:
        lines.extend(_wrap(f"Tailored for {tailored}.", width))
    summary = as_str(meta.get("summary"))
    if summary:
        _heading(lines, "Summary", width)
        lines.extend(_wrap(summary, width))
    _experience(resume.get("experience"), lines, width)
    _projects(resume.get("projects"), lines, width)
    _education(resume.get("education"), lines, width)
    _skills(resume.get("skills"), lines, width)
    return "\n".join(lines).rstrip() + "\n"


def _heading(lines: list[str], title: str, width: int) -> None:
    lines.append("")
    lines.append(title.upper())
    lines.append("-" * min(len(title), width))


def _contact(meta: dict) -> list[str]:
    values = [
        as_str(meta.get("email")),
        as_str(meta.get("phone")),
        as_str(meta.get("location")),
        as_str(meta.get("website")),
    ]
    return [value for value in values if value]


def _experience(entries: object, lines: list[str], width: int) -> None:
    roles = _mappings(entries)
    if not roles:
        return
    _heading(lines, "Experience", width)
    for role in roles:
        lines.append("")
        title = as_str(role.get("title")) or "Role"
        company = as_str(role.get("company"))
        lines.extend(_wrap(f"{title} - {company}" if company else title, width))
        meta_line = _when_where(role)
        if meta_line:
            lines.extend(_wrap(meta_line, width))
        for bullet in string_list(role.get("highlights")):
            lines.extend(_bullet(bullet, width))
        skills = string_list(role.get("skills"))
        if skills:
            lines.extend(_wrap("Skills: " + ", ".join(skills), width))


def _projects(entries: object, lines: list[str], width: int) -> None:
    projects = _mappings(entries)
    if not projects:
        return
    _heading(lines, "Projects", width)
    for project in projects:
        lines.append("")
        lines.extend(_wrap(as_str(project.get("name")) or "Project", width))
        url = as_str(project.get("url"))
        if url:
            lines.extend(_wrap(url, width))
        description = as_str(project.get("description"))
        if description:
            lines.extend(_wrap(description, width))
        for bullet in string_list(project.get("highlights")):
            lines.extend(_bullet(bullet, width))


def _education(entries: object, lines: list[str], width: int) -> None:
    schools = _mappings(entries)
    if not schools:
        return
    _heading(lines, "Education", width)
    for school in schools:
        lines.append("")
        degree = as_str(school.get("degree")) or "Study"
        name = as_str(school.get("school"))
        lines.extend(_wrap(f"{degree} - {name}" if name else degree, width))
        span = _span(school.get("start"), school.get("end"))
        if span:
            lines.extend(_wrap(span, width))
        details = as_str(school.get("details"))
        if details:
            lines.extend(_wrap(details, width))


def _skills(entries: object, lines: list[str], width: int) -> None:
    groups = _mappings(entries)
    visible = []
    for group in groups:
        items = string_list(group.get("items"))
        if items:
            label = as_str(group.get("group")) or "Skills"
            visible.append(f"{label}: " + ", ".join(items))
    if not visible:
        return
    _heading(lines, "Skills", width)
    for line in visible:
        lines.extend(_wrap(line, width))


def _bullet(text: str, width: int) -> list[str]:
    wrapped = _wrap(text, max(20, width - 2))
    if not wrapped:
        return []
    lines = [f"- {wrapped[0]}"]
    lines.extend(f"  {extra}" for extra in wrapped[1:])
    return lines


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        if len(current) + 1 + len(word) <= width:
            current = f"{current} {word}"
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _mappings(entries: object) -> list[dict]:
    if not isinstance(entries, list):
        return []
    return [item for item in entries if isinstance(item, dict)]


def _when_where(entry: dict) -> str:
    span = _span(entry.get("start"), entry.get("end"))
    location = as_str(entry.get("location"))
    return " | ".join(part for part in (span, location) if part)


def _span(start: object, end: object) -> str:
    left = as_str(start)
    right = as_str(end)
    if left and right:
        return f"{left} - {right}"
    return left or right
