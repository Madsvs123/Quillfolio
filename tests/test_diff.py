"""Tests for comparing two resume versions."""

import copy

from quillfolio.cli import main
from quillfolio.diffing import diff_resumes, format_diff
from quillfolio.resume_io import save_resume

from paths import EXAMPLE


def _left() -> dict:
    return {
        "meta": {
            "name": "Marlowe Voss",
            "email": "marlowe.voss@example.com",
            "summary": "Fictional sample.",
        },
        "experience": [
            {
                "id": "cedar-circuit",
                "company": "Cedar Circuit",
                "title": "Engineer",
                "start": "2021-04",
                "end": "present",
                "highlights": ["Kept an invented queue running."],
            }
        ],
    }


def test_diff_reports_email_title_highlight_and_added_role():
    left = _left()
    right = copy.deepcopy(left)
    right["meta"]["email"] = "marlowe.voss+jobs@example.com"
    right["experience"][0]["title"] = "Senior Engineer"
    right["experience"][0]["highlights"] = [
        "Kept an invented queue running.",
        "Added a second invented note.",
    ]
    right["experience"].append(
        {
            "id": "lumen-post",
            "company": "Lumen Post",
            "title": "Advisor",
            "start": "2024-02",
            "highlights": ["Reviewed fictional drafts."],
        }
    )

    changes = diff_resumes(left, right)
    text = format_diff(changes)
    assert "changed meta.email" in text
    assert "  - marlowe.voss@example.com" in text
    assert "  + marlowe.voss+jobs@example.com" in text
    assert "changed experience[cedar-circuit].title" in text
    assert "  - Engineer" in text
    assert "  + Senior Engineer" in text
    assert "added experience[cedar-circuit].highlights" in text
    assert "Added a second invented note." in text
    assert "added experience[lumen-post]" in text
    assert "Advisor @ Lumen Post" in text


def test_diff_reports_a_removed_role():
    left = _left()
    right = copy.deepcopy(left)
    right["experience"] = []
    text = format_diff(diff_resumes(left, right))
    assert "removed experience[cedar-circuit]" in text
    assert "Engineer @ Cedar Circuit" in text


def test_identical_resumes_have_no_differences():
    left = _left()
    assert diff_resumes(left, copy.deepcopy(left)) == []
    assert format_diff([]) == "No differences.\n"


def test_diff_cli_exit_codes(tmp_path):
    left = _left()
    right = copy.deepcopy(left)
    right["meta"]["location"] = "Fictional Harbor, OR"
    left_path = tmp_path / "left.yaml"
    right_path = tmp_path / "right.yaml"
    save_resume(left_path, left)
    save_resume(right_path, right)
    assert main(["diff", str(left_path), str(right_path)]) == 1
    assert main(["diff", str(EXAMPLE), str(EXAMPLE)]) == 0
