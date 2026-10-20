"""Tests for appending a highlight to an existing entry."""

from quillfolio.cli import main
from quillfolio.resume_io import load_resume

from paths import EXAMPLE


def test_add_bullet_appends_to_the_named_role(tmp_path):
    path = tmp_path / "resume.yaml"
    path.write_text(EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    bullet = "Noted a fictional handoff that never happened."
    assert (
        main(
            [
                "add-bullet",
                str(path),
                "--id",
                "cedar-circuit",
                "--highlight",
                bullet,
            ]
        )
        == 0
    )
    highlights = load_resume(path)["experience"][0]["highlights"]
    assert highlights[-1] == bullet
    assert len(highlights) == 3
    assert main(["add-bullet", str(path), "--id", "missing-role", "--highlight", bullet]) == 1
