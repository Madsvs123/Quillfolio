"""Write a local export of the operator's resume."""

from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

from quillfolio.errors import ResumeError
from quillfolio.html_render import THEMES, render_html
from quillfolio.markdown_render import render_markdown
from quillfolio.resume_io import dump_yaml


def export_directory(resume: dict, out_dir: Path | str) -> list[Path]:
    """Write Markdown, JSON, YAML, and each built-in HTML theme into a folder."""
    if not isinstance(resume, dict):
        raise ResumeError("resume must be a mapping")
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    outputs = {
        "resume.md": render_markdown(resume),
        "resume.json": json.dumps(resume, indent=2, ensure_ascii=False) + "\n",
        "resume.yaml": dump_yaml(resume),
    }
    for theme in THEMES:
        outputs[f"resume.{theme}.html"] = render_html(resume, theme)
    written: list[Path] = []
    for name, content in outputs.items():
        path = destination / name
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def export_zip(resume: dict, zip_path: Path | str) -> Path:
    """Write the same export files into a zip archive."""
    destination = Path(zip_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        files = export_directory(resume, Path(tmp))
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file in files:
                archive.write(file, arcname=file.name)
    return destination
