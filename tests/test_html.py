"""Tests for the built-in HTML themes."""

import copy

import pytest

from quillfolio.errors import ResumeError
from quillfolio.html_render import render_html
from quillfolio.resume_io import load_resume

from paths import EXAMPLE


def test_themes_are_distinct_and_self_contained():
    resume = load_resume(EXAMPLE)
    atelier = render_html(resume, "atelier")
    signal = render_html(resume, "signal")
    ledger = render_html(resume, "ledger")
    assert len({atelier, signal, ledger}) == 3
    assert 'class="theme-atelier"' in atelier
    assert 'class="theme-signal"' in signal
    assert 'class="theme-ledger"' in ledger
    assert "Courier" in ledger
    for document in (atelier, signal, ledger):
        assert "Marlowe Voss" in document
        assert "Cedar Circuit" in document
        assert "Lantern Index" in document
        assert "Example University" in document
        assert "fonts.googleapis.com" not in document
        assert "@import" not in document
        assert "<img" not in document
        assert document.count("<style>") == 1
        assert "2021-04" in document
        assert "&ndash;" in document


def test_html_escapes_operator_text():
    resume = load_resume(EXAMPLE)
    resume["meta"]["name"] = "A <b>Name</b> & Co </style><script>alert(1)</script>"
    resume["meta"]["website"] = "javascript:alert(1)"
    document = render_html(resume, "signal")
    assert "<b>Name</b>" not in document
    assert "A &lt;b&gt;Name&lt;/b&gt; &amp; Co" in document
    assert "<script>" not in document
    assert 'href="javascript:' not in document
    assert "javascript:" not in document


def test_print_stylesheet_is_embedded_in_every_theme():
    resume = load_resume(EXAMPLE)
    for theme in ("atelier", "signal", "ledger"):
        document = render_html(resume, theme)
        assert "quillfolio-print" in document
        assert "size: letter" in document
        assert "break-inside: avoid" in document
        assert document.count("<style>") == 1
        assert "<link" not in document


def test_unknown_theme_is_rejected():
    resume = load_resume(EXAMPLE)
    with pytest.raises(ResumeError, match="unknown theme"):
        render_html(resume, "comic-sans")
    untouched = copy.deepcopy(resume)
    with pytest.raises(ResumeError):
        render_html(resume, "signal-extra")
    assert resume == untouched
