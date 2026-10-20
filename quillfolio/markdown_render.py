"""Render a resume as Markdown."""

from __future__ import annotations

from quillfolio.errors import ResumeError
from quillfolio.textutil import as_str, string_list


def render_markdown(resume: dict) -> str:
    """Render the operator's resume as a Markdown document."""
    if not isinstance(resume, dict):
        raise ResumeError("resume must be a mapping")
    meta = resume.get("meta") if isinstance(resume.get("meta"), dict) else {}
    lines: list[str] = []
    name = as_str(meta.get("name")) or "Resume"
    lines.append(f"# {name}")
    lines.append("")
    headline = as_str(meta.get("headline"))
    if headline:
        lines.append(f"**{headline}**")
        lines.append("")
    tailored = as_str(meta.get("tailored_for"))
    if tailored:
        lines.append(f"_Tailored for {tailored}._")
        lines.append("")
    contact = _contact(meta)
    if contact:
        lines.append(" | ".join(contact))
        lines.append("")
    summary = as_str(meta.get("summary"))
    if summary:
        lines.append("## Summary")
        lines.append("")
        lines.append(summary)
        lines.append("")
    _write_experience(resume.get("experience"), lines)
    _write_projects(resume.get("projects"), lines)
    _write_education(resume.get("education"), lines)
    _write_skills(resume.get("skills"), lines)
    return "\n".join(lines).rstrip() + "\n"


def _contact(meta: dict) -> list[str]:
    values = [
        as_str(meta.get("email")),
        as_str(meta.get("phone")),
        as_str(meta.get("location")),
        as_str(meta.get("website")),
    ]
    return [value for value in values if value]


def _write_experience(entries: object, lines: list[str]) -> None:
    roles = _mappings(entries)
    if not roles:
        return
    lines.append("## Experience")
    lines.append("")
    for role in roles:
        title = as_str(role.get("title")) or "Role"
        company = as_str(role.get("company"))
        heading = f"{title} - {company}" if company else title
        lines.append(f"### {heading}")
        lines.append("")
        meta_line = _when_where(role)
        if meta_line:
            lines.append(f"*{meta_line}*")
            lines.append("")
        for bullet in string_list(role.get("highlights")):
            lines.append(f"- {bullet}")
        skills = string_list(role.get("skills"))
        if skills:
            if role.get("highlights"):
                lines.append("")
            lines.append("Skills: " + ", ".join(skills))
        lines.append("")


def _write_projects(entries: object, lines: list[str]) -> None:
    projects = _mappings(entries)
    if not projects:
        return
    lines.append("## Projects")
    lines.append("")
    for project in projects:
        name = as_str(project.get("name")) or "Project"
        lines.append(f"### {name}")
        lines.append("")
        url = as_str(project.get("url"))
        if url:
            lines.append(url)
            lines.append("")
        description = as_str(project.get("description"))
        if description:
            lines.append(description)
            lines.append("")
        for bullet in string_list(project.get("highlights")):
            lines.append(f"- {bullet}")
        skills = string_list(project.get("skills"))
        if skills:
            lines.append("")
            lines.append("Skills: " + ", ".join(skills))
        lines.append("")


def _write_education(entries: object, lines: list[str]) -> None:
    schools = _mappings(entries)
    if not schools:
        return
    lines.append("## Education")
    lines.append("")
    for school in schools:
        degree = as_str(school.get("degree")) or "Study"
        name = as_str(school.get("school"))
        heading = f"{degree} - {name}" if name else degree
        lines.append(f"### {heading}")
        lines.append("")
        span = _span(school.get("start"), school.get("end"))
        if span:
            lines.append(f"*{span}*")
            lines.append("")
        details = as_str(school.get("details"))
        if details:
            lines.append(details)
            lines.append("")


def _write_skills(entries: object, lines: list[str]) -> None:
    groups = _mappings(entries)
    if not groups:
        return
    lines.append("## Skills")
    lines.append("")
    for group in groups:
        label = as_str(group.get("group")) or "Skills"
        items = string_list(group.get("items"))
        if items:
            lines.append(f"**{label}:** " + ", ".join(items))
            lines.append("")


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
