"""Create a starter resume and append roles or projects."""

from __future__ import annotations

import copy
from pathlib import Path

from quillfolio.errors import DateParseError, ResumeError
from quillfolio.resume_io import save_resume
from quillfolio.textutil import as_str, slugify
from quillfolio.validate import canonical_date_text, parse_date

_HEADER = (
    "# Resume for the person running Quillfolio.\n"
    "# Edit this file locally. The tool does not upload it.\n\n"
)


def starter_resume() -> dict:
    """Return a valid placeholder resume the operator replaces with their own history."""
    return {
        "meta": {
            "name": "Your Name",
            "headline": "The role you want next",
            "email": "you@example.com",
            "phone": "+1-555-0100",
            "location": "City, Region",
            "website": "https://example.com",
            "summary": (
                "Replace this starter with your own history. "
                "Quillfolio reads the file on this machine and does not upload it."
            ),
        },
        "experience": [
            {
                "id": "example-role",
                "company": "Example Studio",
                "title": "Role title",
                "location": "City, Region",
                "start": "2022-01",
                "end": "present",
                "skills": ["writing", "planning"],
                "highlights": [
                    "Describe a result you are willing to stand behind.",
                    "Keep each bullet to one or two lines.",
                ],
            }
        ],
        "projects": [
            {
                "id": "example-project",
                "name": "Example Project",
                "url": "https://example.com/project",
                "description": "A short description of something you built.",
                "skills": ["python"],
                "highlights": ["Say what you made and why it mattered."],
            }
        ],
        "education": [
            {
                "school": "Example University",
                "degree": "Degree, Field of study",
                "start": "2016",
                "end": "2020",
                "details": "Optional note, such as a focus or honor.",
            }
        ],
        "skills": [
            {"group": "Tools", "items": ["Python", "Git"]},
        ],
    }


def write_starter(path: Path | str) -> None:
    destination = Path(path)
    save_resume(destination, starter_resume())
    if destination.suffix.lower() in {".yaml", ".yml"}:
        body = destination.read_text(encoding="utf-8")
        destination.write_text(_HEADER + body, encoding="utf-8")


def add_role(
    resume: dict,
    *,
    company: str,
    title: str,
    start: str,
    end: str | None = None,
    location: str | None = None,
    role_id: str | None = None,
    highlights: list[str] | None = None,
    skills: list[str] | None = None,
) -> dict:
    """Return a copy of the resume with one experience entry appended."""
    updated = _copy_resume(resume)
    start_text, end_text = _dates(start, end)
    entry: dict = {
        "id": _unique_id(updated, role_id, f"{company}-{start_text}"),
        "company": _required(company, "company"),
        "title": _required(title, "title"),
        "start": start_text,
    }
    if end_text is not None:
        entry["end"] = end_text
    if location is not None and as_str(location):
        entry["location"] = as_str(location)
    cleaned_skills = _clean_skills(skills)
    if cleaned_skills:
        entry["skills"] = cleaned_skills
    entry["highlights"] = _required_highlights(highlights)
    experience = updated.get("experience")
    if experience is None:
        experience = []
        updated["experience"] = experience
    if not isinstance(experience, list):
        raise ResumeError("experience must be a list")
    experience.append(entry)
    return updated


def add_project(
    resume: dict,
    *,
    name: str,
    url: str | None = None,
    description: str | None = None,
    project_id: str | None = None,
    highlights: list[str] | None = None,
    skills: list[str] | None = None,
) -> dict:
    """Return a copy of the resume with one project appended."""
    updated = _copy_resume(resume)
    entry: dict = {
        "id": _unique_id(updated, project_id, name),
        "name": _required(name, "name"),
    }
    if url is not None and as_str(url):
        entry["url"] = as_str(url)
    if description is not None and as_str(description):
        entry["description"] = as_str(description)
    cleaned_skills = _clean_skills(skills)
    if cleaned_skills:
        entry["skills"] = cleaned_skills
    entry["highlights"] = _required_highlights(highlights)
    projects = updated.get("projects")
    if projects is None:
        projects = []
        updated["projects"] = projects
    if not isinstance(projects, list):
        raise ResumeError("projects must be a list")
    projects.append(entry)
    return updated


def _copy_resume(resume: dict) -> dict:
    if not isinstance(resume, dict):
        raise ResumeError("resume must be a mapping")
    return copy.deepcopy(resume)


def _required(value: str, label: str) -> str:
    text = as_str(value)
    if not text:
        raise ResumeError(f"{label} is required")
    return text


def _required_highlights(highlights: list[str] | None) -> list[str]:
    if not highlights:
        raise ResumeError("at least one highlight is required")
    cleaned: list[str] = []
    for item in highlights:
        text = as_str(item)
        if not text:
            raise ResumeError("highlights must be non-empty text")
        cleaned.append(text)
    return cleaned


def _clean_skills(skills: list[str] | None) -> list[str]:
    cleaned: list[str] = []
    for item in skills or []:
        text = as_str(item)
        if not text:
            raise ResumeError("skills must be non-empty text")
        cleaned.append(text)
    return cleaned


def _dates(start: str, end: str | None) -> tuple[str, str | None]:
    try:
        start_text = canonical_date_text(start, "start")
        if end is None:
            return start_text, None
        if not as_str(end):
            raise DateParseError("end date cannot be blank")
        end_text = canonical_date_text(end, "end")
        start_parsed = parse_date(start_text, "start")
        end_parsed = parse_date(end_text, "end")
        if (
            start_parsed.parts is not None
            and end_parsed.parts is not None
            and end_parsed.parts < start_parsed.parts
        ):
            raise DateParseError("end date is before start date")
    except DateParseError as exc:
        raise ResumeError(str(exc)) from exc
    return start_text, end_text


def _unique_id(resume: dict, preferred: str | None, fallback: str) -> str:
    existing: set[str] = set()
    for section in ("experience", "projects", "education"):
        for item in resume.get(section) or []:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                existing.add(item["id"].strip())
    base = slugify(preferred or fallback) or "item"
    if base not in existing:
        return base
    number = 2
    while f"{base}-{number}" in existing:
        number += 1
    return f"{base}-{number}"
