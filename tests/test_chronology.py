"""Tests for sorting roles and education by date."""

from quillfolio.cli import main
from quillfolio.resume_io import load_resume

from paths import EXAMPLE


def test_sort_command_orders_experience_by_start(tmp_path):
    path = tmp_path / "resume.yaml"
    path.write_text(EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    assert main(["sort", str(path), "--ascending"]) == 0
    assert [role["id"] for role in load_resume(path)["experience"]] == [
        "paperfinch",
        "cedar-circuit",
    ]
    assert main(["sort", str(path)]) == 0
    assert [role["id"] for role in load_resume(path)["experience"]] == [
        "cedar-circuit",
        "paperfinch",
    ]
