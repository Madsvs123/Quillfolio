"""Tests for merging two local resume files."""

import copy

from quillfolio.cli import main
from quillfolio.merge import merge_resumes
from quillfolio.resume_io import load_resume, save_resume

from paths import EXAMPLE


def test_merge_prefers_the_left_file_and_unions_skills(tmp_path):
    left = load_resume(EXAMPLE)
    right = copy.deepcopy(left)
    right["meta"]["name"] = "Someone Else"
    right["meta"]["pronouns"] = "they/them"
    right["experience"].append(
        {
            "id": "lumen-post",
            "company": "Lumen Post",
            "title": "Advisor",
            "start": "2024-01",
            "end": "present",
            "highlights": ["Reviewed fictional drafts."],
        }
    )
    right["skills"][0]["items"].append("Rust")
    merged, notes = merge_resumes(left, right)
    assert merged["meta"]["name"] == "Marlowe Voss"
    assert merged["meta"]["pronouns"] == "they/them"
    assert [role["id"] for role in merged["experience"]].count("cedar-circuit") == 1
    assert merged["experience"][-1]["id"] == "lumen-post"
    assert "Rust" in merged["skills"][0]["items"]
    assert any("cedar-circuit" in note for note in notes)

    left_path = tmp_path / "left.yaml"
    right_path = tmp_path / "right.yaml"
    out_path = tmp_path / "merged.yaml"
    save_resume(left_path, left)
    save_resume(right_path, right)
    assert main(["merge", str(left_path), str(right_path), "--out", str(out_path)]) == 0
    stored = load_resume(out_path)
    assert stored["experience"][-1]["company"] == "Lumen Post"
    assert stored["meta"]["name"] == "Marlowe Voss"
