"""Check a resume mapping for structural problems."""

from __future__ import annotations

import calendar
import datetime as dt
import re
from dataclasses import dataclass

from quillfolio.errors import DateParseError, Issue
from quillfolio.textutil import as_str, is_email, safe_href

_DATE_RE = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")

_ROOT_FIELDS = {"meta", "experience", "projects", "education", "skills"}
_META_FIELDS = {
    "name",
    "headline",
    "email",
    "phone",
    "location",
    "website",
    "summary",
    "tailored_for",
}
_EXPERIENCE_FIELDS = {
    "id",
    "company",
    "title",
    "location",
    "start",
    "end",
    "skills",
    "highlights",
}
_PROJECT_FIELDS = {"id", "name", "url", "description", "skills", "highlights"}
_EDUCATION_FIELDS = {"id", "school", "degree", "start", "end", "details"}
_SKILL_FIELDS = {"group", "items"}


@dataclass(frozen=True)
class ResumeDate:
    present: bool
    parts: tuple[int, int, int] | None


def parse_date(value: object, bound: str) -> ResumeDate:
    """Parse YYYY, YYYY-MM, YYYY-MM-DD, or an end value of present."""
    if bound not in {"start", "end"}:
        raise DateParseError("date bound must be start or end")
    if isinstance(value, str):
        text = value.strip()
    elif isinstance(value, bool) or value is None:
        raise DateParseError("use YYYY, YYYY-MM, or YYYY-MM-DD")
    elif isinstance(value, int):
        text = str(value)
    elif isinstance(value, dt.datetime):
        text = value.date().isoformat()
    elif isinstance(value, dt.date):
        text = value.isoformat()
    else:
        raise DateParseError("use YYYY, YYYY-MM, or YYYY-MM-DD")

    if text.lower() == "present":
        if bound == "start":
            raise DateParseError("start date cannot be present")
        return ResumeDate(True, None)

    match = _DATE_RE.fullmatch(text)
    if not match:
        raise DateParseError("use YYYY, YYYY-MM, or YYYY-MM-DD")
    year = int(match.group(1))
    if year < 1900 or year > 2100:
        raise DateParseError("year must be from 1900 to 2100")
    month_text = match.group(2)
    day_text = match.group(3)
    if month_text is None:
        month = 1 if bound == "start" else 12
        day = 1 if bound == "start" else calendar.monthrange(year, month)[1]
    else:
        month = int(month_text)
        if not 1 <= month <= 12:
            raise DateParseError("month must be from 01 to 12")
        last_day = calendar.monthrange(year, month)[1]
        if day_text is None:
            day = 1 if bound == "start" else last_day
        else:
            day = int(day_text)
            if not 1 <= day <= last_day:
                raise DateParseError("day is not valid for that month")
    return ResumeDate(False, (year, month, day))


def canonical_date_text(value: object, bound: str) -> str:
    """Validate a date and return the text that should be stored."""
    parsed = parse_date(value, bound)
    if parsed.present:
        return "present"
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    assert parsed.parts is not None
    year, month, day = parsed.parts
    return f"{year:04d}-{month:02d}-{day:02d}"


def validate_resume(resume: dict) -> list[Issue]:
    """Return errors and warnings. An empty list means the resume is ready to render."""
    issues: list[Issue] = []
    if not isinstance(resume, dict):
        return [Issue("error", "resume", "resume must be a mapping")]

    for key in resume:
        if key not in _ROOT_FIELDS:
            issues.append(Issue("warning", str(key), "unknown field; themes ignore it"))

    meta = _mapping(resume, "meta", issues, required=True)
    if meta is not None:
        _validate_meta(meta, issues)

    experience = _section(resume, "experience", issues)
    projects = _section(resume, "projects", issues)
    education = _section(resume, "education", issues)
    seen_ids: dict[str, str] = {}

    if experience is not None:
        for index, entry in enumerate(experience):
            _validate_experience(entry, index, issues, seen_ids)
    if projects is not None:
        for index, entry in enumerate(projects):
            _validate_project(entry, index, issues, seen_ids)
    if education is not None:
        for index, entry in enumerate(education):
            _validate_education(entry, index, issues, seen_ids)
    if "skills" in resume:
        _validate_skills(resume["skills"], issues)

    if experience is not None and projects is not None and not experience and not projects:
        issues.append(Issue("warning", "experience", "add at least one role or project"))
    return issues


def _mapping(resume: dict, key: str, issues: list[Issue], *, required: bool) -> dict | None:
    if key not in resume:
        if required:
            issues.append(Issue("error", key, f"{key} is required"))
        return None
    value = resume[key]
    if not isinstance(value, dict):
        issues.append(Issue("error", key, f"{key} must be a mapping"))
        return None
    return value


def _section(resume: dict, key: str, issues: list[Issue]) -> list | None:
    if key not in resume:
        return []
    value = resume[key]
    if not isinstance(value, list):
        issues.append(Issue("error", key, f"{key} must be a list"))
        return None
    return value


def _validate_meta(meta: dict, issues: list[Issue]) -> None:
    for key in meta:
        if key not in _META_FIELDS:
            issues.append(Issue("warning", f"meta.{key}", "unknown meta field"))
    name = meta.get("name")
    if not isinstance(name, str) or not name.strip():
        issues.append(Issue("error", "meta.name", "name is required"))
    _optional_text(meta, "headline", "meta.headline", "headline", issues)
    _optional_text(meta, "summary", "meta.summary", "summary", issues)
    _optional_text(meta, "tailored_for", "meta.tailored_for", "tailored_for", issues)
    _optional_text(meta, "location", "meta.location", "location", issues)

    if "email" in meta:
        email = meta.get("email")
        if not isinstance(email, str) or not email.strip():
            issues.append(Issue("error", "meta.email", "email must be non-empty text"))
        elif not is_email(email.strip()):
            issues.append(Issue("error", "meta.email", "email address is not valid"))

    if "phone" in meta:
        phone = meta.get("phone")
        if not isinstance(phone, str) or not phone.strip():
            issues.append(
                Issue("error", "meta.phone", "quote the phone number so it stays text")
            )

    if "website" in meta:
        website = meta.get("website")
        if not isinstance(website, str) or not website.strip():
            issues.append(Issue("error", "meta.website", "website must be non-empty text"))
        elif safe_href(website) is None:
            issues.append(
                Issue(
                    "error",
                    "meta.website",
                    "website must start with http://, https://, or mailto:",
                )
            )

    channels = [
        as_str(meta.get("email")),
        as_str(meta.get("phone")) if isinstance(meta.get("phone"), str) else "",
        as_str(meta.get("location")),
        as_str(meta.get("website")),
    ]
    if not any(channels):
        issues.append(Issue("error", "meta", "add an email, phone, location, or website"))


def _validate_experience(
    entry: object,
    index: int,
    issues: list[Issue],
    seen_ids: dict[str, str],
) -> None:
    path = f"experience[{index}]"
    if not isinstance(entry, dict):
        issues.append(Issue("error", path, "experience entries must be mappings"))
        return
    path = _note_id(entry, path, seen_ids, issues)
    _known_fields(entry, _EXPERIENCE_FIELDS, path, issues)
    _require_text(entry, "company", path, "company", issues)
    _require_text(entry, "title", path, "title", issues)
    _optional_text(entry, "location", f"{path}.location", "location", issues)
    _validate_dates(entry, path, issues, start_required=True)
    _validate_text_list(entry, "highlights", path, issues, "add at least one highlight")
    if "skills" in entry:
        _validate_text_list(entry, "skills", path, issues, "add at least one skill or remove the list")


def _validate_project(
    entry: object,
    index: int,
    issues: list[Issue],
    seen_ids: dict[str, str],
) -> None:
    path = f"projects[{index}]"
    if not isinstance(entry, dict):
        issues.append(Issue("error", path, "project entries must be mappings"))
        return
    path = _note_id(entry, path, seen_ids, issues)
    _known_fields(entry, _PROJECT_FIELDS, path, issues)
    _require_text(entry, "name", path, "name", issues)
    _optional_text(entry, "description", f"{path}.description", "description", issues)
    if "url" in entry:
        url = entry.get("url")
        if not isinstance(url, str) or not url.strip():
            issues.append(Issue("error", f"{path}.url", "url must be non-empty text"))
        elif safe_href(url) is None:
            issues.append(
                Issue("error", f"{path}.url", "url must start with http://, https://, or mailto:")
            )
    _validate_text_list(entry, "highlights", path, issues, "add at least one highlight")
    if "skills" in entry:
        _validate_text_list(entry, "skills", path, issues, "add at least one skill or remove the list")


def _validate_education(
    entry: object,
    index: int,
    issues: list[Issue],
    seen_ids: dict[str, str],
) -> None:
    path = f"education[{index}]"
    if not isinstance(entry, dict):
        issues.append(Issue("error", path, "education entries must be mappings"))
        return
    if "id" in entry:
        path = _note_id(entry, path, seen_ids, issues)
    _known_fields(entry, _EDUCATION_FIELDS, path, issues)
    _require_text(entry, "school", path, "school", issues)
    _require_text(entry, "degree", path, "degree", issues)
    _optional_text(entry, "details", f"{path}.details", "details", issues)
    if "start" in entry or "end" in entry:
        _validate_dates(entry, path, issues, start_required="start" in entry)


def _validate_skills(value: object, issues: list[Issue]) -> None:
    if not isinstance(value, list):
        issues.append(Issue("error", "skills", "skills must be a list of groups"))
        return
    seen: dict[str, str] = {}
    for index, group in enumerate(value):
        path = f"skills[{index}]"
        if not isinstance(group, dict):
            issues.append(Issue("error", path, "skill group must be a mapping"))
            continue
        _known_fields(group, _SKILL_FIELDS, path, issues)
        name = group.get("group")
        if not isinstance(name, str) or not name.strip():
            issues.append(Issue("error", f"{path}.group", "group name is required"))
        else:
            label = name.strip()
            path = f"skills[{label}]"
            key = label.lower()
            if key in seen:
                issues.append(Issue("error", f"{path}.group", f"duplicate skill group {label!r}"))
            else:
                seen[key] = path
        if "items" not in group:
            issues.append(Issue("error", f"{path}.items", "items are required"))
        else:
            _validate_text_list(
                group,
                "items",
                path,
                issues,
                "add at least one skill",
            )


def _validate_dates(entry: dict, path: str, issues: list[Issue], *, start_required: bool) -> None:
    start_parsed: ResumeDate | None = None
    if "start" not in entry or _blank(entry.get("start")):
        if start_required:
            issues.append(Issue("error", f"{path}.start", "start date is required"))
    else:
        try:
            start_parsed = parse_date(entry.get("start"), "start")
        except DateParseError as exc:
            issues.append(Issue("error", f"{path}.start", str(exc)))

    if "end" not in entry or entry.get("end") is None or _blank(entry.get("end")):
        issues.append(Issue("warning", f"{path}.end", "add an end date or present"))
        return
    try:
        end_parsed = parse_date(entry.get("end"), "end")
    except DateParseError as exc:
        issues.append(Issue("error", f"{path}.end", str(exc)))
        return
    if (
        start_parsed is not None
        and start_parsed.parts is not None
        and end_parsed.parts is not None
        and end_parsed.parts < start_parsed.parts
    ):
        issues.append(Issue("error", f"{path}.end", "end date is before start date"))


def _validate_text_list(
    entry: dict,
    field: str,
    path: str,
    issues: list[Issue],
    empty_message: str,
) -> None:
    target = f"{path}.{field}"
    if field not in entry:
        issues.append(Issue("warning", target, empty_message))
        return
    value = entry[field]
    if not isinstance(value, list):
        issues.append(Issue("error", target, f"{field} must be a list of strings"))
        return
    if not value:
        issues.append(Issue("warning", target, empty_message))
        return
    for index, item in enumerate(value):
        if isinstance(item, str) and item.strip():
            continue
        issues.append(Issue("error", f"{target}[{index}]", f"{field} must be non-empty text"))


def _note_id(entry: dict, path: str, seen_ids: dict[str, str], issues: list[Issue]) -> str:
    if "id" not in entry:
        issues.append(Issue("warning", f"{path}.id", "add an id so later diffs stay stable"))
        return path
    ident = entry.get("id")
    if not isinstance(ident, str) or not ident.strip():
        issues.append(Issue("error", f"{path}.id", "id must be non-empty text"))
        return path
    cleaned = ident.strip()
    if cleaned in seen_ids:
        issues.append(
            Issue(
                "error",
                f"{path}.id",
                f"duplicate id {cleaned!r} (also used at {seen_ids[cleaned]})",
            )
        )
    else:
        seen_ids[cleaned] = path
    if not _ID_RE.fullmatch(cleaned):
        issues.append(
            Issue(
                "warning",
                f"{path}.id",
                "id should use letters, numbers, hyphens, or underscores",
            )
        )
    return f"{path.split('[')[0]}[{cleaned}]"


def _known_fields(entry: dict, known: set[str], path: str, issues: list[Issue]) -> None:
    for key in entry:
        if key not in known:
            issues.append(Issue("warning", f"{path}.{key}", "unknown field; themes ignore it"))


def _require_text(entry: dict, field: str, path: str, label: str, issues: list[Issue]) -> None:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        issues.append(Issue("error", f"{path}.{field}", f"{label} is required"))


def _optional_text(entry: dict, field: str, path: str, label: str, issues: list[Issue]) -> None:
    if field not in entry:
        return
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        issues.append(Issue("error", path, f"{label} must be non-empty text"))


def _blank(value: object) -> bool:
    return isinstance(value, str) and not value.strip()
