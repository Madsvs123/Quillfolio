"""Tests for the command-line commands that rewrite a local resume."""

import zipfile

from quillfolio.cli import main
from quillfolio.resume_io import load_resume, save_resume
from quillfolio.validate import validate_resume

from paths import EXAMPLE


def test_init_validate_add_and_export(tmp_path):
    path = tmp_path / "resume.yaml"
    assert main(["init", str(path)]) == 0
    text = path.read_text(encoding="utf-8")
    assert "does not upload" in text
    assert main(["validate", str(path)]) == 0
    assert validate_resume(load_resume(path)) == []
    assert main(["init", str(path)]) == 1

    before = path.read_text(encoding="utf-8")
    rejected = main(
        [
            "add-role",
            str(path),
            "--company",
            "Lumen Post",
            "--title",
            "Advisor",
            "--start",
            "2024-05",
            "--end",
            "2020-01",
            "--highlight",
            "This date range is impossible.",
        ]
    )
    assert rejected == 1
    assert path.read_text(encoding="utf-8") == before

    assert (
        main(
            [
                "add-role",
                str(path),
                "--company",
                "Lumen Post",
                "--title",
                "Advisor",
                "--start",
                "2024-05",
                "--end",
                "present",
                "--highlight",
                "Reviewed fictional drafts for this test.",
                "--skill",
                "editing",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "add-project",
                str(path),
                "--name",
                "Second Example",
                "--url",
                "https://example.com/second",
                "--highlight",
                "Another fictional bullet.",
                "--skill",
                "python",
            ]
        )
        == 0
    )
    loaded = load_resume(path)
    assert loaded["experience"][-1]["company"] == "Lumen Post"
    assert loaded["experience"][-1]["start"] == "2024-05"
    assert loaded["projects"][-1]["name"] == "Second Example"
    assert validate_resume(loaded) == []

    out = tmp_path / "dist"
    archive = tmp_path / "bundle.zip"
    assert main(["export", str(path), "--out", str(out), "--zip", str(archive)]) == 0
    for name in (
        "resume.md",
        "resume.json",
        "resume.yaml",
        "resume.atelier.html",
        "resume.signal.html",
        "resume.ledger.html",
    ):
        assert (out / name).is_file()
    assert "Your Name" in (out / "resume.md").read_text(encoding="utf-8")
    assert "theme-atelier" in (out / "resume.atelier.html").read_text(encoding="utf-8")
    assert "theme-signal" in (out / "resume.signal.html").read_text(encoding="utf-8")
    assert "theme-ledger" in (out / "resume.ledger.html").read_text(encoding="utf-8")
    with zipfile.ZipFile(archive) as bundle:
        names = set(bundle.namelist())
    assert "resume.md" in names
    assert "resume.signal.html" in names


def test_validate_strict_and_render_html_theme(tmp_path):
    path = tmp_path / "resume.yaml"
    assert main(["init", str(path)]) == 0
    resume = load_resume(path)
    resume["experience"][0].pop("highlights")
    save_resume(path, resume)
    assert main(["validate", str(path)]) == 0
    assert main(["validate", str(path), "--strict"]) == 1

    html_path = tmp_path / "resume.html"
    assert main(["render-html", str(EXAMPLE), "--theme", "signal", "--out", str(html_path)]) == 0
    assert "theme-signal" in html_path.read_text(encoding="utf-8")
    missing = tmp_path / "missing.html"
    assert main(["render-html", str(EXAMPLE), "--theme", "nope", "--out", str(missing)]) == 1
    assert not missing.exists()
