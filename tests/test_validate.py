"""Tests for resume validation."""

import copy

from quillfolio.resume_io import load_resume, save_resume
from quillfolio.validate import validate_resume

from paths import EXAMPLE, ROOT


def test_example_resume_is_valid_and_fictional():
    resume = load_resume(EXAMPLE)
    assert validate_resume(resume) == []
    assert resume["meta"]["name"] == "Marlowe Voss"
    assert resume["meta"]["email"] == "marlowe.voss@example.com"
    assert resume["meta"]["email"].endswith("@example.com")


def test_validate_does_not_mutate():
    resume = load_resume(EXAMPLE)
    snapshot = copy.deepcopy(resume)
    validate_resume(resume)
    assert resume == snapshot


def test_missing_name_is_an_error():
    resume = load_resume(EXAMPLE)
    resume["meta"]["name"] = "  "
    issues = validate_resume(resume)
    assert any(issue.severity == "error" and issue.path == "meta.name" for issue in issues)


def test_bad_email_is_an_error():
    resume = load_resume(EXAMPLE)
    resume["meta"]["email"] = "not-an-email"
    issues = validate_resume(resume)
    assert any(issue.path == "meta.email" and "not valid" in issue.message for issue in issues)


def test_end_before_start_is_an_error():
    resume = load_resume(EXAMPLE)
    resume["experience"][0]["start"] = "2022-05"
    resume["experience"][0]["end"] = "2020-01"
    issues = validate_resume(resume)
    assert any(issue.severity == "error" and "before" in issue.message for issue in issues)


def test_same_year_and_present_are_accepted():
    resume = load_resume(EXAMPLE)
    resume["experience"][0]["start"] = "2020"
    resume["experience"][0]["end"] = "2020"
    issues = validate_resume(resume)
    assert not any("before" in issue.message for issue in issues)
    resume["experience"][0]["end"] = "present"
    issues = validate_resume(resume)
    assert not any(issue.severity == "error" and "end" in issue.path for issue in issues)


def test_impossible_day_is_an_error():
    resume = load_resume(EXAMPLE)
    resume["experience"][0]["start"] = "2021-02-31"
    issues = validate_resume(resume)
    assert any("day is not valid" in issue.message for issue in issues)


def test_duplicate_id_is_an_error():
    resume = load_resume(EXAMPLE)
    resume["projects"][0]["id"] = resume["experience"][0]["id"]
    issues = validate_resume(resume)
    assert any(issue.severity == "error" and "duplicate id" in issue.message for issue in issues)


def test_experience_must_be_a_list():
    resume = load_resume(EXAMPLE)
    resume["experience"] = "Cedar Circuit"
    issues = validate_resume(resume)
    assert any(issue.severity == "error" and issue.path == "experience" for issue in issues)


def test_json_roundtrip_stays_valid(tmp_path):
    resume = load_resume(EXAMPLE)
    path = tmp_path / "resume.json"
    save_resume(path, resume)
    loaded = load_resume(path)
    assert loaded["meta"]["email"] == "marlowe.voss@example.com"
    assert validate_resume(loaded) == []


def test_public_docs_name_the_license_holder():
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Copyright (c) 2026 Madsvs123" in license_text
    assert "MIT License" in license_text
    for command in (
        "init",
        "validate",
        "add-role",
        "add-project",
        "tailor",
        "render-md",
        "render-html",
        "diff",
        "export",
        "preview",
    ):
        assert command in readme
    assert "local" in readme.lower()
