"""Tests for skills grouped by category."""

from quillfolio.cli import main
from quillfolio.resume_io import load_resume
from quillfolio.skills import add_skill, format_skills

from paths import EXAMPLE


def test_skills_command_groups_the_sample():
    text = format_skills(load_resume(EXAMPLE))
    assert text.startswith("Languages\n- Python\n- Go\n- SQL\n")
    assert "Practices\n- Testing\n- Technical writing\n- Incident notes\n" in text


def test_add_skill_extends_a_category_and_rejects_duplicates(tmp_path):
    path = tmp_path / "resume.yaml"
    path.write_text(EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    assert main(["add-skill", str(path), "--group", "languages", "--item", "Rust"]) == 0
    loaded = load_resume(path)
    languages = loaded["skills"][0]
    assert languages["group"] == "Languages"
    assert languages["items"][-1] == "Rust"
    created = add_skill(loaded, "Field notes", "Indexing")
    assert created["skills"][-1] == {"group": "Field notes", "items": ["Indexing"]}
    assert main(["add-skill", str(path), "--group", "Languages", "--item", "rust"]) == 1
