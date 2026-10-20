"""Tests for the local quillfolio.yaml config file."""

from quillfolio.cli import main
from quillfolio.config import load_config
from quillfolio.resume_io import load_resume

from paths import EXAMPLE


def test_missing_config_uses_atelier_and_no_name(tmp_path):
    config = load_config(tmp_path / "resume.yaml")
    assert config.path is None
    assert config.theme == "atelier"
    assert config.name is None


def test_config_sets_the_init_name_and_the_html_theme(tmp_path):
    folder = tmp_path / "drafts"
    folder.mkdir()
    (folder / "quillfolio.yaml").write_text(
        "theme: ledger\nname: Sable Quinn\n",
        encoding="utf-8",
    )
    resume_path = folder / "resume.yaml"
    assert main(["init", str(resume_path)]) == 0
    assert load_resume(resume_path)["meta"]["name"] == "Sable Quinn"

    sample = folder / "sample.yaml"
    sample.write_text(EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    html_path = folder / "resume.html"
    assert main(["render-html", str(sample), "--out", str(html_path)]) == 0
    assert "theme-ledger" in html_path.read_text(encoding="utf-8")
    shown = load_config(sample)
    assert shown.theme == "ledger"
    assert shown.name == "Sable Quinn"
