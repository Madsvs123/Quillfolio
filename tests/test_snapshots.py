"""Tests for on-disk resume snapshots."""

import pytest

from quillfolio.cli import main
from quillfolio.errors import ResumeError
from quillfolio.snapshots import list_snapshots, take_snapshot

from paths import EXAMPLE


def test_snapshot_and_restore_round_trip(tmp_path, capsys):
    path = tmp_path / "resume.yaml"
    path.write_text(EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    saved = take_snapshot(path, "before-edit")
    assert saved.number == "0001"
    path.write_text("meta:\n  name: Changed\n", encoding="utf-8")
    assert main(["snapshots", str(path)]) == 0
    listed = capsys.readouterr().out
    assert "0001" in listed
    assert "before-edit" in listed
    assert main(["restore", str(path), "--label", "before-edit"]) == 0
    assert "Marlowe Voss" in path.read_text(encoding="utf-8")
    assert "Changed" not in path.read_text(encoding="utf-8")


def test_snapshot_refuses_a_duplicate_label_unless_forced(tmp_path):
    path = tmp_path / "resume.yaml"
    path.write_text("one\n", encoding="utf-8")
    assert main(["snapshot", str(path), "--label", "first"]) == 0
    path.write_text("two\n", encoding="utf-8")
    with pytest.raises(ResumeError, match="already exists"):
        take_snapshot(path, "first")
    assert main(["snapshot", str(path), "--label", "first", "--force"]) == 0
    stored = list_snapshots(path)
    assert len(stored) == 1
    assert stored[0].label == "first"
