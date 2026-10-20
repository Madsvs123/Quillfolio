"""Draft a cover letter from the operator's own resume file."""

from __future__ import annotations

from quillfolio.errors import ResumeError
from quillfolio.textutil import as_str, string_list


def render_cover_letter(resume: dict, *, role: str, company: str) -> str:
    """Write a plain-text letter using only fields already in the resume.

    The letter stays on this machine. It does not look up the company or
    send the resume anywhere.
    """
    if not isinstance(resume, dict):
        raise ResumeError("resume must be a mapping")
    role_text = as_str(role)
    company_text = as_str(company)
    if not role_text:
        raise ResumeError("role is required")
    if not company_text:
        raise ResumeError("company is required")

    meta = resume.get("meta") if isinstance(resume.get("meta"), dict) else {}
    name = as_str(meta.get("name")) or "Your Name"
    lines: list[str] = [name]
    contact = [
        as_str(meta.get("email")),
        as_str(meta.get("phone")),
        as_str(meta.get("location")),
        as_str(meta.get("website")),
    ]
    contact = [item for item in contact if item]
    if contact:
        lines.append(" | ".join(contact))
    lines.append("")
    lines.append(f"Dear {company_text} team,")
    lines.append("")

    headline = as_str(meta.get("headline"))
    opening = f"I am writing about the {role_text} role at {company_text}."
    if headline:
        opening = f"{opening} {headline}."
    lines.append(opening)
    lines.append("")

    summary = as_str(meta.get("summary"))
    if summary:
        lines.append(summary)
        lines.append("")

    evidence = _evidence(resume.get("experience"))
    if evidence:
        lines.append("Work from this resume that I would draw on:")
        lines.append("")
        lines.extend(evidence)
        lines.append("")

    lines.append("The details above come from my local resume file.")
    lines.append("")
    lines.append("Sincerely,")
    lines.append(name)
    return "\n".join(lines).rstrip() + "\n"


def _evidence(entries: object) -> list[str]:
    if not isinstance(entries, list):
        return []
    lines: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict) or len(lines) >= 3:
            break
        title = as_str(entry.get("title")) or "Role"
        company = as_str(entry.get("company"))
        where = f"{title} at {company}" if company else title
        highlights = string_list(entry.get("highlights"))
        if highlights:
            lines.append(f"- {where}: {highlights[0]}")
        else:
            lines.append(f"- {where}")
    return lines
