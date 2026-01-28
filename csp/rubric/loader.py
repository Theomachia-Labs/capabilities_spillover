"""Rubric loading and basic validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

RUBRIC_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class RubricDimension:
    id: str
    name: str
    description: str
    anchors: dict[str, str]


@dataclass(frozen=True)
class Rubric:
    version: str
    name: str
    dimensions: list[RubricDimension]


def _validate_rubric(data: dict[str, Any]) -> None:
    required_fields = {"version", "name", "dimensions"}
    missing = required_fields - data.keys()
    if missing:
        raise ValueError(f"Rubric missing required fields: {sorted(missing)}")
    if not isinstance(data["dimensions"], list) or not data["dimensions"]:
        raise ValueError("Rubric dimensions must be a non-empty list")
    for dim in data["dimensions"]:
        for field in ("id", "name", "description", "anchors"):
            if field not in dim:
                raise ValueError(f"Dimension missing field: {field}")


def load_rubric(path: Path | str) -> Rubric:
    """Load a rubric YAML file and return a typed Rubric object."""
    path = Path(path)
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("Rubric file must parse to a mapping")
    _validate_rubric(data)

    dimensions = [
        RubricDimension(
            id=dim["id"],
            name=dim["name"],
            description=dim["description"],
            anchors={str(k): str(v) for k, v in dim.get("anchors", {}).items()},
        )
        for dim in data["dimensions"]
    ]
    return Rubric(version=str(data["version"]), name=str(data["name"]), dimensions=dimensions)


def load_default_rubric() -> Rubric:
    """Load the default rubric bundled with the package."""
    return load_rubric(RUBRIC_DIR / "rubric_v1.yaml")
