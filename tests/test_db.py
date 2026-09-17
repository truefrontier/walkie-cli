"""Tests for database layer."""

import pytest
from walkie_cli.db import WalkieDB


def test_get_status(fixture_db):
    """Test status information retrieval."""
    db = WalkieDB(db_path=fixture_db)
    status = db.get_status()
    
    assert status["meeting_count"] == 2
    assert status["segment_count"] == 6
    assert status["dictation_count"] == 2
    assert "db_path" in status
    db.close()


def test_list_meetings(fixture_db):
    """Test listing meetings."""
    db = WalkieDB(db_path=fixture_db)
    meetings = db.list_meetings()
    
    assert len(meetings) == 2
    assert meetings[0]["title"] == "Design Review"  # Most recent first
    assert meetings[1]["title"] == "Team Standup"
    assert meetings[0]["segment_count"] == 2
    assert meetings[1]["segment_count"] == 4
    db.close()


def test_list_meetings_with_limit(fixture_db):
    """Test listing meetings with limit."""
    db = WalkieDB(db_path=fixture_db)
    meetings = db.list_meetings(limit=1)
    
    assert len(meetings) == 1
    assert meetings[0]["title"] == "Design Review"
    db.close()


def test_get_meeting_by_id(fixture_db):
    """Test getting meeting by exact ID."""
    db = WalkieDB(db_path=fixture_db)
    meeting = db.get_meeting("mtg-001")
    
    assert meeting is not None
    assert meeting["title"] == "Team Standup"
    assert meeting["source"] == "zoom"
    assert meeting["status"] == "ready"
    assert meeting["segment_count"] == 4
    assert len(meeting["action_items"]) == 1
    assert meeting["action_items"][0]["text"] == "Review PR #123"
    db.close()


def test_get_meeting_by_title_substring(fixture_db):
    """Test getting meeting by title substring."""
    db = WalkieDB(db_path=fixture_db)
    meeting = db.get_meeting("standup")
    
    assert meeting is not None
    assert meeting["title"] == "Team Standup"
    db.close()


def test_get_meeting_not_found(fixture_db):
    """Test getting non-existent meeting."""
    db = WalkieDB(db_path=fixture_db)
    meeting = db.get_meeting("nonexistent")
    
    assert meeting is None
    db.close()


def test_get_meeting_transcript(fixture_db):
    """Test getting meeting transcript."""
    db = WalkieDB(db_path=fixture_db)
    transcript = db.get_meeting_transcript("mtg-001")
    
    assert len(transcript) == 4
    assert transcript[0]["speaker"] == "you"
    assert transcript[0]["text"] == "Good morning everyone!"
    assert transcript[1]["speaker"] == "them:1"
    assert "time" in transcript[0]
    db.close()


def test_get_meeting_transcript_with_limit(fixture_db):
    """Test getting meeting transcript with limit."""
    db = WalkieDB(db_path=fixture_db)
    transcript = db.get_meeting_transcript("mtg-001", limit=2)
    
    assert len(transcript) == 2
    db.close()


def test_get_meeting_transcript_by_title(fixture_db):
    """Test getting transcript by title substring."""
    db = WalkieDB(db_path=fixture_db)
    transcript = db.get_meeting_transcript("design")
    
    assert len(transcript) == 2
    assert transcript[0]["text"] == "Let's review the new dashboard design."
    db.close()


def test_list_dictations(fixture_db):
    """Test listing dictations."""
    db = WalkieDB(db_path=fixture_db)
    dictations = db.list_dictations()
    
    assert len(dictations) == 2
    assert dictations[0]["title"] == "Quick note"  # Most recent first
    assert dictations[1]["title"] == "Todo for today"
    assert dictations[1]["app"] == "VS Code"
    db.close()


def test_list_dictations_with_limit(fixture_db):
    """Test listing dictations with limit."""
    db = WalkieDB(db_path=fixture_db)
    dictations = db.list_dictations(limit=1)
    
    assert len(dictations) == 1
    db.close()
