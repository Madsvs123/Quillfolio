"""Tests for the resume stats command."""

import datetime as dt

from quillfolio.cli import main
from quillfolio.resume_io import load_resume
from quillfolio.stats import resume_stats

from paths import EXAMPLE


def test_stats_count_roles_words_and_years():
    stats = resume_stats(load_resume(EXAMPLE), today=dt.date(2026, 4, 1))
    assert stats.roles == 2
    assert stats.projects == 2
    assert stats.schools == 1
    assert stats.skills == 6
    assert stats.bullets == 7
    assert stats.words > 40
    # 2018-06 through 2021-03 is 33 months, and 2021-04 through 2026-04 is 60.
    assert stats.years == 7.8


def test_stats_command_prints_the_summary(capsys):
    assert main(["stats", str(EXAMPLE)]) == 0
    text = capsys.readouterr().out
    assert "roles: 2" in text
    assert "projects: 2" in text
    assert "words: " in text
    assert "years: " in text
