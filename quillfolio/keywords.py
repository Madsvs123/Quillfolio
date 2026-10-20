"""Compare a local resume with a local job-description text file."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from quillfolio.errors import ResumeError

MAX_JOB_BYTES = 1_000_000
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9+#]*")
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "but",
        "by",
        "for",
        "from",
        "has",
        "have",
        "in",
        "into",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "our",
        "that",
        "the",
        "their",
        "this",
        "to",
        "we",
        "will",
        "with",
        "you",
        "your",
        "about",
        "ability",
        "across",
        "also",
        "can",
        "experience",
        "including",
        "job",
        "role",
        "skills",
        "strong",
        "team",
        "using",
        "work",
        "working",
        "years",
    }
)


@dataclass(frozen=True)
class Coverage:
    """Keywords from a job description that do or do not appear in the resume."""

    present: tuple[str, ...]
    missing: tuple[str, ...]

    @property
    def total(self) -> int:
        return len(self.present) + len(self.missing)

    @property
    def percent(self) -> int:
        if self.total == 0:
            return 100
        return round(100 * len(self.present) / self.total)


def load_job_text(path: Path | str) -> str:
    """Read a job description from a local UTF-8 text file."""
    source = Path(path)
    if not source.is_file():
        raise ResumeError(f"file not found: {source}")
    size = source.stat().st_size
    if size > MAX_JOB_BYTES:
        raise ResumeError(f"job description is larger than {MAX_JOB_BYTES} bytes: {source}")
    try:
        return source.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ResumeError(f"job description must be UTF-8: {source}") from exc


def keyword_coverage(resume: dict, job_text: str, *, min_length: int = 4) -> Coverage:
    """Return job keywords that appear, as whole words, in the resume text."""
    if not isinstance(resume, dict):
        raise ResumeError("resume must be a mapping")
    if isinstance(min_length, bool) or not isinstance(min_length, int) or not 2 <= min_length <= 32:
        raise ResumeError("min length must be an integer from 2 to 32")
    if not isinstance(job_text, str):
        raise ResumeError("job description must be text")
    corpus = _corpus(resume)
    present: list[str] = []
    missing: list[str] = []
    for word in _keywords(job_text, min_length):
        pattern = re.compile(rf"(?<![a-z0-9]){re.escape(word)}(?![a-z0-9])")
        if pattern.search(corpus):
            present.append(word)
        else:
            missing.append(word)
    return Coverage(tuple(present), tuple(missing))


def format_coverage(report: Coverage) -> str:
    present = ", ".join(report.present) if report.present else "(none)"
    missing = ", ".join(report.missing) if report.missing else "(none)"
    lines = [
        f"coverage: {len(report.present)}/{report.total} ({report.percent}%)",
        f"present: {present}",
        f"missing: {missing}",
    ]
    return "\n".join(lines) + "\n"


def _keywords(text: str, min_length: int) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for match in _WORD_RE.finditer(text):
        word = match.group(0).casefold()
        if len(word) < min_length or word in _STOPWORDS or word in seen:
            continue
        seen.add(word)
        found.append(word)
    return found


def _corpus(value: object) -> str:
    chunks: list[str] = []

    def walk(item: object) -> None:
        if isinstance(item, str):
            chunks.append(item)
        elif isinstance(item, dict):
            for child in item.values():
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)
    return "\n".join(chunks).casefold()
