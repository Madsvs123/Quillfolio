"""Errors and validation issues for a local resume file."""

from __future__ import annotations

from dataclasses import dataclass


class ResumeError(Exception):
    """The resume file could not be read, checked, or updated."""


class DateParseError(ValueError):
    """A resume date was missing or not in a supported form."""


@dataclass(frozen=True)
class Issue:
    """One problem found while checking a resume."""

    severity: str
    path: str
    message: str

    def format(self, source: str | None = None) -> str:
        where = f"{source}: " if source else ""
        return f"{self.severity}: {where}{self.path}: {self.message}"
