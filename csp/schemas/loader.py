"""Load and validate CSP JSON schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

SCHEMA_DIR = Path(__file__).resolve().parent
SCHEMA_MAP = {
    "csp_score": "csp_score.schema.json",
    "paper_record": "paper_record.schema.json",
    "label_record": "label_record.schema.json",
    "survey_response": "survey_response.schema.json",
}


def load_schema(name: str) -> dict[str, Any]:
    if name not in SCHEMA_MAP:
        raise KeyError(f"Unknown schema name: {name}")
    schema_path = SCHEMA_DIR / SCHEMA_MAP[name]
    return json.loads(schema_path.read_text())


def validate_instance(instance: dict[str, Any], schema_name: str) -> None:
    """Validate a JSON-like instance against a named schema.

    Raises jsonschema.ValidationError on failure.
    """
    schema = load_schema(schema_name)
    Draft7Validator(schema).validate(instance)
