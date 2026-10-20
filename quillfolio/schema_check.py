"""Validate a resume mapping against the bundled JSON Schema."""

from __future__ import annotations

import json
import re
from pathlib import Path

from quillfolio.errors import ResumeError

_SCHEMA_NAME = "resume.schema.json"


def schema_path() -> Path:
    return Path(__file__).with_name(_SCHEMA_NAME)


def load_schema() -> dict:
    """Load the JSON Schema document shipped with Quillfolio."""
    path = schema_path()
    if not path.is_file():
        raise ResumeError("JSON Schema is missing from the install")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ResumeError(f"JSON Schema is invalid: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ResumeError("JSON Schema must be a mapping")
    return data


def schema_text() -> str:
    path = schema_path()
    if not path.is_file():
        raise ResumeError("JSON Schema is missing from the install")
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    return text


def schema_errors(instance: object, schema: dict | None = None) -> list[str]:
    """Return schema violations. An empty list means the instance matches."""
    document = load_schema() if schema is None else schema
    if not isinstance(document, dict):
        raise ResumeError("JSON Schema must be a mapping")
    errors: list[str] = []
    _check(instance, document, "", errors)
    return errors


def _check(instance: object, schema: dict, path: str, errors: list[str]) -> None:
    expected = schema.get("type")
    if isinstance(expected, str) and not _matches_type(instance, expected):
        where = path or "<root>"
        errors.append(f"{where}: expected {expected}")
        return
    if isinstance(instance, str):
        _check_string(instance, schema, path or "<root>", errors)
    elif isinstance(instance, list):
        _check_array(instance, schema, path or "<root>", errors)
    elif isinstance(instance, dict):
        _check_object(instance, schema, path, errors)


def _check_string(instance: str, schema: dict, path: str, errors: list[str]) -> None:
    minimum = schema.get("minLength")
    if isinstance(minimum, int) and len(instance) < minimum:
        errors.append(f"{path}: must be at least {minimum} character(s)")
    pattern = schema.get("pattern")
    if isinstance(pattern, str) and re.search(pattern, instance) is None:
        errors.append(f"{path}: does not match {pattern}")


def _check_array(instance: list, schema: dict, path: str, errors: list[str]) -> None:
    minimum = schema.get("minItems")
    if isinstance(minimum, int) and len(instance) < minimum:
        errors.append(f"{path}: must contain at least {minimum} item(s)")
    item_schema = schema.get("items")
    if isinstance(item_schema, dict):
        for index, item in enumerate(instance):
            _check(item, item_schema, f"{path}[{index}]", errors)


def _check_object(instance: dict, schema: dict, path: str, errors: list[str]) -> None:
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        properties = {}
    required = schema.get("required")
    if isinstance(required, list):
        for key in required:
            if isinstance(key, str) and key not in instance:
                child = f"{path}.{key}" if path else key
                errors.append(f"{child}: required property is missing")
    additional = schema.get("additionalProperties", True)
    for key, value in instance.items():
        child = f"{path}.{key}" if path else str(key)
        if key in properties and isinstance(properties[key], dict):
            _check(value, properties[key], child, errors)
        elif additional is False:
            errors.append(f"{child}: additional property is not allowed")
        elif isinstance(additional, dict):
            _check(value, additional, child, errors)


def _matches_type(instance: object, expected: str) -> bool:
    if expected == "string":
        return isinstance(instance, str)
    if expected == "object":
        return isinstance(instance, dict)
    if expected == "array":
        return isinstance(instance, list)
    if expected == "boolean":
        return isinstance(instance, bool)
    if expected == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if expected == "null":
        return instance is None
    return False
