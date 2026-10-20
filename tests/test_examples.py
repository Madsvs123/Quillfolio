"""Tests for the fictional example resumes."""

from quillfolio.html_render import render_html
from quillfolio.linting import lint_resume
from quillfolio.resume_io import load_resume
from quillfolio.schema_check import schema_errors
from quillfolio.validate import validate_resume

from paths import ROOT

SABLE = ROOT / "examples" / "sable-quinn.yaml"


def test_sable_quinn_is_a_second_fictional_profile():
    resume = load_resume(SABLE)
    assert resume["meta"]["name"] == "Sable Quinn"
    assert resume["meta"]["email"].endswith("@example.com")
    assert "fictional" in resume["meta"]["summary"].lower()
    assert validate_resume(resume) == []
    assert lint_resume(resume) == []
    assert schema_errors(resume) == []
    document = render_html(resume, "ledger")
    assert "Sable Quinn" in document
    assert "Kindling Press" in document
    assert "Margin Notes" in document
