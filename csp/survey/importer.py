"""Survey import functionality."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from csp.schemas.loader import validate_instance
from csp.survey.models import SurveyResponse


def import_from_json(db: Session, json_path: Path | str) -> list[SurveyResponse]:
    """Import survey responses from a JSON file.
    
    Args:
        db: Database session
        json_path: Path to JSON file containing array of survey responses
        
    Returns:
        List of created SurveyResponse objects
    """
    json_path = Path(json_path)
    with open(json_path) as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        data = [data]
    
    responses = []
    for record in data:
        response = import_response(db, record)
        responses.append(response)
    
    return responses


def import_from_csv(db: Session, csv_path: Path | str) -> list[SurveyResponse]:
    """Import survey responses from a CSV file.
    
    Expects columns: respondent_id, topic, dimension_id, score, uncertainty
    Groups rows by respondent_id to create SurveyResponse objects.
    """
    csv_path = Path(csv_path)
    
    # Group by respondent
    respondent_data: dict[str, dict[str, dict[str, dict]]] = {}
    
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            resp_id = row["respondent_id"]
            topic = row["topic"]
            dim_id = row["dimension_id"]
            
            if resp_id not in respondent_data:
                respondent_data[resp_id] = {}
            if topic not in respondent_data[resp_id]:
                respondent_data[resp_id][topic] = {}
            
            respondent_data[resp_id][topic][dim_id] = {
                "score": float(row["score"]),
                "uncertainty": float(row.get("uncertainty", 0.5)),
            }
    
    # Create response objects
    responses = []
    for respondent_id, topics in respondent_data.items():
        record = {
            "response_id": f"resp_{respondent_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "respondent_id": respondent_id,
            "created_at": datetime.now().isoformat(),
            "responses": [
                {"topic": topic, "dimensions": dims}
                for topic, dims in topics.items()
            ]
        }
        response = import_response(db, record)
        responses.append(response)
    
    return responses


def import_response(db: Session, record: dict[str, Any]) -> SurveyResponse:
    """Import a single survey response.
    
    Validates against schema and stores in database.
    """
    # Validate against schema
    validate_instance(record, "survey_response")
    
    # Extract calibration if present
    calibration = record.get("calibration", {})
    
    db_obj = SurveyResponse(
        response_id=record["response_id"],
        respondent_id=record["respondent_id"],
        created_at=record["created_at"],
        calibration_score=calibration.get("score") if calibration else None,
        calibration_notes=calibration.get("notes") if calibration else None,
        responses=record["responses"],
    )
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_responses_for_topic(db: Session, topic: str) -> list[SurveyResponse]:
    """Get all responses that include a specific topic."""
    from sqlalchemy import select
    
    all_responses = db.execute(select(SurveyResponse)).scalars().all()
    
    # Filter to those containing the topic
    matching = []
    for response in all_responses:
        for resp in response.responses:
            if resp.get("topic") == topic:
                matching.append(response)
                break
    
    return matching
