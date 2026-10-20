"""Command-level tests for the newer local Quillfolio commands."""

import copy

from quillfolio.cli import main
from quillfolio.html_render import render_html
from quillfolio.resume_io import load_resume, save_resume

from paths import EXAMPLE, ROOT

SABLE = ROOT / "examples" / "sable-quinn.yaml"


def test_cover_letter_rejects_a_blank_role(capsys):
    assert main(["cover-letter", str(EXAMPLE), "--role", "   ", "--company", "Archive"]) == 1
    assert "role is required" in capsys.readouterr().err


def test_reorder_sections_from_the_cli(tmp_path):
    path = tmp_path / "resume.yaml"
    save_resume(path, load_resume(EXAMPLE))
    assert main(["reorder", str(path), "--section", "skills", "--section", "meta"]) == 0
    assert list(load_resume(path))[:2] == ["skills", "meta"]
    assert main(["reorder", str(path), "--section", "nope"]) == 1


def test_keywords_fail_under_zero_still_prints_missing_words(tmp_path, capsys):
    job = tmp_path / "job.txt"
    job.write_text("Seeking someone who has used kubernetes and python.\n", encoding="utf-8")
    assert main(["keywords", str(SABLE), str(job), "--fail-under", "0"]) == 0
    text = capsys.readouterr().out
    assert "kubernetes" in text
    assert "coverage:" in text


def test_restore_by_snapshot_id(tmp_path):
    path = tmp_path / "resume.yaml"
    original = "name: Before\n"
    path.write_text(original, encoding="utf-8")
    assert main(["snapshot", str(path), "--label", "kept"]) == 0
    path.write_text("name: After\n", encoding="utf-8")
    assert main(["restore", str(path), "--id", "1"]) == 0
    assert path.read_text(encoding="utf-8") == original


def test_schema_accepts_both_example_profiles():
    assert main(["schema", str(EXAMPLE)]) == 0
    assert main(["schema", str(SABLE)]) == 0


def test_render_txt_rejects_a_narrow_width(tmp_path):
    assert main(["render-txt", str(EXAMPLE), "--width", "10", "--out", str(tmp_path / "out.txt")]) == 1
    assert not (tmp_path / "out.txt").exists()


def test_merge_notes_a_duplicate_id(tmp_path, capsys):
    left = tmp_path / "left.yaml"
    right = tmp_path / "right.yaml"
    out = tmp_path / "merged.yaml"
    save_resume(left, load_resume(EXAMPLE))
    right_resume = load_resume(EXAMPLE)
    extra = copy.deepcopy(right_resume["experience"][0])
    extra["id"] = "kindling-press"
    extra["company"] = "Kindling Press"
    right_resume["experience"].append(extra)
    save_resume(right, right_resume)
    assert main(["merge", str(left), str(right), "--out", str(out)]) == 0
    notes = capsys.readouterr().err
    assert "cedar-circuit" in notes
    ids = [role["id"] for role in load_resume(out)["experience"]]
    assert ids.count("cedar-circuit") == 1
    assert "kindling-press" in ids


def test_lint_and_stats_on_the_writing_example(capsys):
    assert main(["lint", str(SABLE)]) == 0
    assert main(["stats", str(SABLE)]) == 0
    text = capsys.readouterr().out
    assert "ok: " in text
    assert "roles: 2" in text
    assert "projects: 2" in text


def test_config_command_reports_a_file_beside_the_resume(tmp_path, capsys):
    resume = tmp_path / "resume.yaml"
    save_resume(resume, load_resume(EXAMPLE))
    (tmp_path / "quillfolio.yaml").write_text("theme: signal\nname: Your Name\n", encoding="utf-8")
    assert main(["config", "--resume", str(resume)]) == 0
    text = capsys.readouterr().out
    assert "theme: signal" in text
    assert "name: Your Name" in text


def test_doctor_without_a_resume_checks_the_install():
    assert main(["doctor"]) == 0


def test_sort_keeps_an_undated_role_at_the_end(tmp_path):
    resume = load_resume(EXAMPLE)
    resume["experience"].append(
        {
            "id": "undated",
            "company": "Example Desk",
            "title": "Assistant",
            "highlights": ["Held a fictional pen."],
        }
    )
    path = tmp_path / "resume.yaml"
    save_resume(path, resume)
    assert main(["sort", str(path), "--ascending"]) == 0
    ids = [role["id"] for role in load_resume(path)["experience"]]
    assert ids[-1] == "undated"
    assert ids[0] == "paperfinch"


def test_add_bullet_can_target_a_project(tmp_path):
    path = tmp_path / "resume.yaml"
    save_resume(path, load_resume(SABLE))
    bullet = "Added a fictional index note."
    assert main(["add-bullet", str(path), "--id", "quiet-index", "--highlight", bullet]) == 0
    project = load_resume(path)["projects"][1]
    assert project["id"] == "quiet-index"
    assert project["highlights"][-1] == bullet


def test_html_themes_embed_the_print_stylesheet_for_the_second_profile():
    resume = load_resume(SABLE)
    for theme in ("atelier", "signal", "ledger"):
        document = render_html(resume, theme)
        assert "Sable Quinn" in document
        assert "quillfolio-print" in document
        assert "size: letter" in document


def test_skills_command_prints_categories(capsys):
    assert main(["skills", str(SABLE)]) == 0
    text = capsys.readouterr().out
    assert text.startswith("Writing\n- Editing\n")
    assert "Tools\n- Markdown\n- Git\n" in text
