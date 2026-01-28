"""Tests for the SQLite storage layer."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from csp.data.db import Base
from csp.data import crud, models

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_create_and_get_paper(db_session: Session):
    paper_data = {
        "paper_id": "test_001",
        "title": "Test Paper",
        "abstract": "This is a test abstract.",
        "year": 2023,
        "identifiers": {"doi": "10.1234/test"},
        "authors": [{"name": "Jane Doe"}],
        "citations": ["ref_001", "ref_002"]
    }
    
    # Create
    created = crud.create_paper(db_session, paper_data)
    assert created.paper_id == "test_001"
    assert created.title == "Test Paper"
    
    # Retrieve
    retrieved = crud.get_paper(db_session, "test_001")
    assert retrieved is not None
    assert retrieved.paper_id == "test_001"
    assert retrieved.identifiers["doi"] == "10.1234/test"

def test_create_and_get_score(db_session: Session):
    score_data = {
        "score_id": "score_001",
        "paper_id": "test_001",
        "rubric_version": "1.0",
        "dimensions": {
            "dim1": {
                "score": 3, 
                "uncertainty": 0.1, 
                "rationale": "Test rationale",
                "evidence": []
            }
        },
        "provenance": {
            "method": "human",
            "created_at": "2023-01-01T00:00:00Z"
        }
    }
    
    # Create
    created = crud.create_score(db_session, score_data)
    assert created.score_id == "score_001"
    
    # Retrieve
    retrieved = crud.get_score(db_session, "score_001")
    assert retrieved is not None
    assert retrieved.dimensions["dim1"]["score"] == 3
