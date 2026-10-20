"""Tests for the resume lint command."""

from quillfolio.cli import main
from quillfolio.linting import lint_resume
from quillfolio.resume_io import load_resume, save_resume

from paths import EXAMPLE


def test_sample_resume_has_no_lint_findings():
    assert lint_resume(load_resume(EXAMPLE)) == []


def test_lint_reports_missing_dates_and_empty_bullets(tmp_path):
    resume = load_resume(EXAMPLE)
    resume["experience"][0].pop("end")
    resume["experience"][0]["highlights"] = ["  "]
    resume["projects"][0]["highlights"] = []
    path = tmp_path / "resume.yaml"
    save_resume(path, resume)
    findings = lint_resume(load_resume(path))
    messages = [issue.message for issue in findings]
    assert messages.count("missing date") == 1
    assert messages.count("empty bullets") == 2
    assert main(["lint", str(path)]) == 1
