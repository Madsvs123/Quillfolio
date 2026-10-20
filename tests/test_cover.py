"""Tests for the local cover-letter command."""

from quillfolio.cli import main
from quillfolio.cover import render_cover_letter
from quillfolio.resume_io import load_resume

from paths import EXAMPLE


def test_cover_letter_uses_the_resume_and_the_role():
    letter = render_cover_letter(
        load_resume(EXAMPLE),
        role="Systems engineer",
        company="Northwind Archive",
    )
    assert letter.startswith("Marlowe Voss\n")
    assert "Dear Northwind Archive team," in letter
    assert "Systems engineer" in letter
    assert "Cedar Circuit" in letter
    assert "marlowe.voss@example.com" in letter
    assert letter.rstrip().endswith("Marlowe Voss")
    assert "example.com" in letter


def test_cover_letter_command_writes_a_file(tmp_path):
    destination = tmp_path / "letter.txt"
    assert (
        main(
            [
                "cover-letter",
                str(EXAMPLE),
                "--role",
                "Observability engineer",
                "--company",
                "Paper Museum",
                "--out",
                str(destination),
            ]
        )
        == 0
    )
    body = destination.read_text(encoding="utf-8")
    assert "Paper Museum" in body
    assert "Observability engineer" in body
    assert "Lantern Index" not in body
