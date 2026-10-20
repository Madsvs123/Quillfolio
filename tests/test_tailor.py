"""Tests for selecting resume sections for a target role."""

import copy

from quillfolio.cli import main
from quillfolio.resume_io import load_resume
from quillfolio.tailor import tailor_resume
from quillfolio.validate import validate_resume

from paths import EXAMPLE


def test_tailor_keeps_python_work_and_drops_the_rest():
    original = load_resume(EXAMPLE)
    snapshot = copy.deepcopy(original)
    result = tailor_resume(original, "Python observability")

    assert original == snapshot
    assert result.kept_role_ids == ["cedar-circuit"]
    assert result.dropped_role_ids == ["paperfinch"]
    assert result.kept_project_ids == ["lantern-index"]
    assert result.dropped_project_ids == ["tide-ledger"]
    assert result.resume["meta"]["tailored_for"] == "Python observability"
    assert result.resume["education"][0]["school"] == "Example University"
    assert [group["group"] for group in result.resume["skills"]] == ["Languages"]
    assert result.resume["skills"][0]["items"][0] == "Python"
    errors = [issue for issue in validate_resume(result.resume) if issue.severity == "error"]
    assert errors == []


def test_keyword_can_supply_a_word_the_role_omits():
    resume = load_resume(EXAMPLE)
    result = tailor_resume(resume, "platform services", keywords=["python"])
    assert result.kept_role_ids == ["cedar-circuit"]
    assert "paperfinch" in result.dropped_role_ids
    assert result.kept_project_ids == ["lantern-index"]


def test_max_roles_keeps_the_earlier_tie():
    resume = load_resume(EXAMPLE)
    result = tailor_resume(resume, "Engineer", max_roles=1)
    assert result.kept_role_ids == ["cedar-circuit"]
    assert result.dropped_role_ids == ["paperfinch"]
    assert any("kept 1 of" in note for note in result.notes)


def test_unrelated_role_clears_experience_and_projects():
    resume = load_resume(EXAMPLE)
    result = tailor_resume(resume, "underwater basket weaving")
    assert result.resume["experience"] == []
    assert result.resume["projects"] == []
    assert any("no experience" in note for note in result.notes)
    assert any("no project" in note for note in result.notes)
    assert any("skill" in note for note in result.notes)
    assert len(result.resume["skills"]) == 2


def test_tailor_cli_writes_the_subset(tmp_path):
    destination = tmp_path / "tailored.yaml"
    status = main(
        ["tailor", str(EXAMPLE), "--role", "Python observability", "--out", str(destination)]
    )
    assert status == 0
    tailored = load_resume(destination)
    assert [item["id"] for item in tailored["experience"]] == ["cedar-circuit"]
    assert tailored["meta"]["tailored_for"] == "Python observability"
    assert "Paperfinch" not in destination.read_text(encoding="utf-8")
