"""Tests for the plain-text resume export."""

from quillfolio.cli import main
from quillfolio.plain_render import render_plain
from quillfolio.resume_io import load_resume

from paths import EXAMPLE


def test_plain_text_lists_the_fictional_resume():
    text = render_plain(load_resume(EXAMPLE), width=40)
    assert text.startswith("Marlowe Voss\n")
    assert "SUMMARY" in text
    assert "EXPERIENCE" in text
    assert "Cedar Circuit" in text
    assert "Lantern Index" in text
    assert "Imaginary Engineering" in text
    assert "University" in text
    assert "Languages: Python, Go, SQL" in text
    assert "#" not in text.splitlines()[0]
    assert all(len(line) <= 40 for line in text.splitlines())
    assert text.endswith("\n")


def test_render_txt_command_writes_a_file(tmp_path):
    destination = tmp_path / "resume.txt"
    assert main(["render-txt", str(EXAMPLE), "--width", "60", "--out", str(destination)]) == 0
    body = destination.read_text(encoding="utf-8")
    assert "Marlowe Voss" in body
    assert "Paperfinch Studio" in body
    assert all(len(line) <= 60 for line in body.splitlines())
