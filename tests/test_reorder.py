"""Tests for reordering sections and entries."""

from quillfolio.cli import main
from quillfolio.reorder import reorder_entries, reorder_sections
from quillfolio.resume_io import load_resume

from paths import EXAMPLE


def test_reorder_sections_puts_named_sections_first():
    resume = load_resume(EXAMPLE)
    updated = reorder_sections(resume, ["skills", "projects"])
    assert list(updated)[:2] == ["skills", "projects"]
    assert list(updated) == ["skills", "projects", "meta", "experience", "education"]
    assert resume["experience"][0]["id"] == "cedar-circuit"


def test_reorder_entries_command(tmp_path):
    source = tmp_path / "resume.yaml"
    source.write_text((EXAMPLE).read_text(encoding="utf-8"), encoding="utf-8")
    assert (
        main(
            [
                "reorder",
                str(source),
                "--entries",
                "experience",
                "--id",
                "paperfinch",
                "--id",
                "cedar-circuit",
            ]
        )
        == 0
    )
    loaded = load_resume(source)
    assert [role["id"] for role in loaded["experience"]] == ["paperfinch", "cedar-circuit"]
    again = reorder_entries(loaded, "experience", ["cedar-circuit"])
    assert [role["id"] for role in again["experience"]] == ["cedar-circuit", "paperfinch"]
