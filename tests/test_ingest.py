"""Tests for ingestion pipeline."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from csp.data.db import Base
from csp.data import models
from csp.ingest import core
from csp.ingest.mock_adapter import MockSourceAdapter

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

def test_ingest_paper_success(db_session):
    mock_data = {
        "paper_123": {
            "paper_id": "paper_123",
            "title": "Safety in ALM",
            "year": 2024
        }
    }
    adapter = MockSourceAdapter(mock_data)
    
    paper = core.ingest_paper(db_session, adapter, "paper_123")
    
    assert paper.paper_id == "paper_123"
    assert paper.title == "Safety in ALM"
    
    # Verify in DB
    saved = db_session.get(models.Paper, "paper_123")
    assert saved is not None

def test_ingest_paper_idempotent(db_session):
    mock_data = {
        "paper_123": {
            "paper_id": "paper_123",
            "title": "Safety in ALM",
            "year": 2024
        }
    }
    adapter = MockSourceAdapter(mock_data)
    
    # First ingest
    p1 = core.ingest_paper(db_session, adapter, "paper_123")
    # Second ingest
    p2 = core.ingest_paper(db_session, adapter, "paper_123")
    
    assert p1.paper_id == p2.paper_id
    # Should be the same object ID if session identity map is active, 
    # but at least same content.
    assert p1 is p2 

def test_ingest_paper_not_found(db_session):
    adapter = MockSourceAdapter({})
    with pytest.raises(ValueError):
        core.ingest_paper(db_session, adapter, "missing_id")
