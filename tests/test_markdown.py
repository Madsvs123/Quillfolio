"""Tests for Markdown rendering."""

from quillfolio.cli import main
from quillfolio.markdown_render import render_markdown
from quillfolio.resume_io import load_resume
from quillfolio.tailor import tailor_resume

from paths import EXAMPLE


def test_render_markdown_includes_the_fictional_resume():
    text = render_markdown(load_resume(EXAMPLE))
    assert text.startswith("# Marlowe Voss\n")
    assert "## Summary\n" in text
    assert "## Experience\n" in text
    assert "## Projects\n" in text
    assert "## Education\n" in text
    assert "## Skills\n" in text
    assert "Cedar Circuit" in text
    assert "Paperfinch Studio" in text
    assert "Lantern Index" in text
    assert "Tide Ledger" in text
    assert "marlowe.voss@example.com" in text
    assert "Example University" in text
    assert "**Languages:** Python, Go, SQL" in text
    assert "Tailored for" not in text
    assert text.endswith("\n")


def test_render_markdown_marks_a_tailored_resume():
    result = tailor_resume(load_resume(EXAMPLE), "Python observability")
    text = render_markdown(result.resume)
    assert "_Tailored for Python observability._" in text
    assert "Cedar Circuit" in text
    assert "Lantern Index" in text
    assert "Paperfinch Studio" not in text
    assert "Tide Ledger" not in text


def test_render_md_cli_writes_a_file(tmp_path):
    destination = tmp_path / "resume.md"
    status = main(["render-md", str(EXAMPLE), "--out", str(destination)])
    assert status == 0
    text = destination.read_text(encoding="utf-8")
    assert "# Marlowe Voss" in text
    assert "Lantern Index" in text
