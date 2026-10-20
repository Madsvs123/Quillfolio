"""Tests for JSON Schema validation."""

from quillfolio.cli import main
from quillfolio.resume_io import load_resume, save_resume
from quillfolio.schema_check import schema_errors, schema_text

from paths import EXAMPLE


def test_sample_resume_matches_the_schema():
    assert schema_errors(load_resume(EXAMPLE)) == []
    shown = schema_text()
    assert '"$schema"' in shown
    assert "Quillfolio resume" in shown


def test_schema_command_rejects_an_unknown_field(tmp_path):
    resume = load_resume(EXAMPLE)
    resume["meta"]["nickname"] = "Mars"
    path = tmp_path / "resume.yaml"
    save_resume(path, resume)
    assert main(["schema", str(path)]) == 1
    assert any("nickname" in error for error in schema_errors(resume))
    assert main(["schema", "--show"]) == 0
