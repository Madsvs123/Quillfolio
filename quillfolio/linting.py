"""Flag missing dates and empty bullets in a local resume."""

from __future__ import annotations

from quillfolio.errors import Issue, ResumeError


def lint_resume(resume: dict) -> list[Issue]:
    """Return editorial errors for dates and bullets.

    Experience and education need both a start and an end (`present` counts).
    Experience and projects need at least one non-empty highlight.
    """
    if not isinstance(resume, dict):
        raise ResumeError("resume must be a mapping")
    issues: list[Issue] = []
    _entries(resume.get("experience"), "experience", issues, dates=True, bullets=True)
    _entries(resume.get("projects"), "projects", issues, dates=False, bullets=True)
    _entries(resume.get("education"), "education", issues, dates=True, bullets=False)
    return issues


def _entries(entries: object, section: str, issues: list[Issue], *, dates: bool, bullets: bool) -> None:
    if entries is None:
        return
    if not isinstance(entries, list):
        issues.append(Issue("error", section, f"{section} must be a list"))
        return
    for index, entry in enumerate(entries):
        path = f"{section}[{index}]"
        if not isinstance(entry, dict):
            issues.append(Issue("error", path, f"{section} entries must be mappings"))
            continue
        ident = entry.get("id")
        if isinstance(ident, str) and ident.strip():
            path = f"{section}[{ident.strip()}]"
        if dates:
            _require_date(entry, "start", path, issues)
            _require_date(entry, "end", path, issues)
        if bullets:
            _require_bullets(entry, path, issues)


def _require_date(entry: dict, field: str, path: str, issues: list[Issue]) -> None:
    if field not in entry or _blank(entry.get(field)):
        issues.append(Issue("error", f"{path}.{field}", "missing date"))


def _require_bullets(entry: dict, path: str, issues: list[Issue]) -> None:
    highlights = entry.get("highlights")
    target = f"{path}.highlights"
    if not isinstance(highlights, list) or not highlights:
        issues.append(Issue("error", target, "empty bullets"))
        return
    for index, item in enumerate(highlights):
        if not isinstance(item, str) or not item.strip():
            issues.append(Issue("error", f"{target}[{index}]", "empty bullets"))


def _blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False
