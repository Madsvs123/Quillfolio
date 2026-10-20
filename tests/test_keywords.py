"""Tests for keyword coverage against a local job description."""

from quillfolio.cli import main
from quillfolio.keywords import format_coverage, keyword_coverage
from quillfolio.resume_io import load_resume

from paths import EXAMPLE

_JOB = """\
Northwind Archive is hiring a Python engineer.
The work involves observability and careful notes.
Kubernetes experience would be welcome.
"""


def test_keyword_coverage_splits_present_and_missing_words():
    report = keyword_coverage(load_resume(EXAMPLE), _JOB, min_length=4)
    assert "python" in report.present
    assert "observability" in report.present
    assert "kubernetes" in report.missing
    assert "the" not in report.present and "the" not in report.missing
    text = format_coverage(report)
    assert text.startswith("coverage: ")
    assert "kubernetes" in text


def test_keywords_command_can_fail_under_a_threshold(tmp_path, capsys):
    job = tmp_path / "job.txt"
    job.write_text(_JOB, encoding="utf-8")
    assert main(["keywords", str(EXAMPLE), str(job), "--fail-under", "90"]) == 1
    captured = capsys.readouterr()
    assert "python" in captured.out
    assert "kubernetes" in captured.out
