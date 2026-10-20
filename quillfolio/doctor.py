"""Check the local install and, when asked, one resume file."""

from __future__ import annotations

import sys
from pathlib import Path

from quillfolio import __version__
from quillfolio.config import load_config
from quillfolio.errors import ResumeError
from quillfolio.html_render import load_print_css, render_html, theme_names
from quillfolio.linting import lint_resume
from quillfolio.mutate import starter_resume
from quillfolio.resume_io import load_resume
from quillfolio.schema_check import load_schema, schema_errors
from quillfolio.validate import validate_resume


def doctor(resume_path: Path | str | None = None) -> tuple[list[str], list[str]]:
    """Return ``(ok_lines, error_lines)`` for the install and an optional resume.

    The checks stay on this machine. They import the local package, read the
    bundled stylesheet and schema, and optionally read one resume file.
    """
    oks: list[str] = []
    errors: list[str] = []

    version = sys.version.split()[0]
    if sys.version_info >= (3, 10):
        oks.append(f"python {version}")
    else:
        errors.append(f"python {version} is older than 3.10")

    try:
        import yaml
    except ImportError:
        errors.append("PyYAML is not installed")
    else:
        oks.append(f"PyYAML {getattr(yaml, '__version__', 'present')}")

    oks.append(f"quillfolio {__version__}")
    _check_assets(oks, errors)
    _check_config(resume_path, oks, errors)
    if resume_path is not None:
        _check_resume(Path(resume_path), oks, errors)
    return oks, errors


def format_doctor(oks: list[str], errors: list[str]) -> str:
    lines = [f"ok: {item}" for item in oks]
    lines.extend(f"error: {item}" for item in errors)
    return "\n".join(lines) + ("\n" if lines else "")


def _check_assets(oks: list[str], errors: list[str]) -> None:
    try:
        css = load_print_css()
    except ResumeError as exc:
        errors.append(str(exc))
    else:
        if "quillfolio-print" in css and "@media print" in css:
            oks.append("print stylesheet")
        else:
            errors.append("print stylesheet is incomplete")

    try:
        schema = load_schema()
    except ResumeError as exc:
        errors.append(str(exc))
    else:
        if schema.get("title") == "Quillfolio resume":
            oks.append("JSON Schema")
        else:
            errors.append("JSON Schema is incomplete")

    starter = starter_resume()
    problems = [issue for issue in validate_resume(starter) if issue.severity == "error"]
    try:
        structural = schema_errors(starter)
    except ResumeError as exc:
        errors.append(str(exc))
        structural = ["schema"]
    if problems or structural:
        errors.append("starter resume does not validate")
    else:
        oks.append("starter resume")

    for theme in theme_names():
        try:
            document = render_html(starter, theme)
        except ResumeError as exc:
            errors.append(f"theme {theme}: {exc}")
            continue
        if f"theme-{theme}" in document and "quillfolio-print" in document:
            oks.append(f"theme {theme}")
        else:
            errors.append(f"theme {theme} did not render")


def _check_config(resume_path: Path | str | None, oks: list[str], errors: list[str]) -> None:
    try:
        config = load_config(resume_path)
    except ResumeError as exc:
        errors.append(str(exc))
        return
    if config.path is None:
        oks.append("config (none)")
    else:
        oks.append(f"config {config.path}")


def _check_resume(path: Path, oks: list[str], errors: list[str]) -> None:
    try:
        resume = load_resume(path)
    except ResumeError as exc:
        errors.append(str(exc))
        return
    validation = [issue for issue in validate_resume(resume) if issue.severity == "error"]
    if validation:
        errors.append(f"{path.name}: {len(validation)} validation error(s)")
    else:
        oks.append(f"resume {path.name}")
    try:
        structural = schema_errors(resume)
    except ResumeError as exc:
        errors.append(str(exc))
        structural = []
    if structural:
        errors.append(f"{path.name}: {len(structural)} schema error(s)")
    else:
        oks.append(f"schema {path.name}")
    try:
        editorial = lint_resume(resume)
    except ResumeError as exc:
        errors.append(str(exc))
        return
    if editorial:
        errors.append(f"{path.name}: {len(editorial)} lint error(s)")
    else:
        oks.append(f"lint {path.name}")
