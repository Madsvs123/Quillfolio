"""Tests for the doctor command."""

from quillfolio.cli import main

from paths import EXAMPLE


def test_doctor_checks_the_install_and_a_resume(capsys):
    assert main(["doctor", str(EXAMPLE)]) == 0
    text = capsys.readouterr().out
    assert "ok: python" in text
    assert "ok: PyYAML" in text
    assert "ok: quillfolio" in text
    assert "ok: print stylesheet" in text
    assert "ok: JSON Schema" in text
    assert "ok: theme ledger" in text
    assert "ok: resume sample-resume.yaml" in text
    assert "ok: lint sample-resume.yaml" in text
    assert "error:" not in text


def test_doctor_fails_when_the_resume_is_incomplete(tmp_path):
    path = tmp_path / "resume.yaml"
    path.write_text('meta:\n  name: ""\n', encoding="utf-8")
    assert main(["doctor", str(path)]) == 1
