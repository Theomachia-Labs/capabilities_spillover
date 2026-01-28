import json
from pathlib import Path

import pytest

from csp.schemas import validate_instance

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.mark.parametrize(
    "schema_name,fixture_name",
    [
        ("csp_score", "csp_score.json"),
        ("paper_record", "paper_record.json"),
        ("label_record", "label_record.json"),
        ("survey_response", "survey_response.json"),
    ],
)
def test_schema_validation(schema_name: str, fixture_name: str) -> None:
    instance = json.loads((FIXTURES / fixture_name).read_text())
    validate_instance(instance, schema_name)
