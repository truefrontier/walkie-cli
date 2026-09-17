"""Tests for CLI interface."""

import json

from click.testing import CliRunner
from walkie_cli.cli import main


def test_status_command(fixture_db):
    """Test status command."""
    runner = CliRunner()
    result = runner.invoke(main, ["--db", str(fixture_db), "--format", "json", "status"])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["meeting_count"] == 2
    assert data["segment_count"] == 6


def test_meetings_list(fixture_db):
    """Test meetings list command."""
    runner = CliRunner()
    result = runner.invoke(main, ["--db", str(fixture_db), "--format", "json", "meetings", "list"])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    assert data[0]["title"] == "Design Review"


def test_meetings_list_with_limit(fixture_db):
    """Test meetings list with limit."""
    runner = CliRunner()
    result = runner.invoke(main, [
        "--db", str(fixture_db),
        "--format", "json",
        "meetings", "list",
        "--limit", "1"
    ])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1


def test_meetings_show(fixture_db):
    """Test meetings show command."""
    runner = CliRunner()
    result = runner.invoke(main, [
        "--db", str(fixture_db),
        "--format", "json",
        "meetings", "show", "mtg-001"
    ])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["title"] == "Team Standup"
    assert data["segment_count"] == 4


def test_meetings_show_by_title(fixture_db):
    """Test meetings show with title substring."""
    runner = CliRunner()
    result = runner.invoke(main, [
        "--db", str(fixture_db),
        "--format", "json",
        "meetings", "show", "design"
    ])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["title"] == "Design Review"


def test_meetings_get_alias(fixture_db):
    """Test meetings get (alias for show)."""
    runner = CliRunner()
    result = runner.invoke(main, [
        "--db", str(fixture_db),
        "--format", "json",
        "meetings", "get", "mtg-001"
    ])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["title"] == "Team Standup"


def test_meetings_transcript(fixture_db):
    """Test meetings transcript command."""
    runner = CliRunner()
    result = runner.invoke(main, [
        "--db", str(fixture_db),
        "--format", "json",
        "meetings", "transcript", "mtg-001"
    ])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 4
    assert data[0]["speaker"] == "you"
    assert data[0]["text"] == "Good morning everyone!"


def test_meetings_transcript_with_limit(fixture_db):
    """Test meetings transcript with limit."""
    runner = CliRunner()
    result = runner.invoke(main, [
        "--db", str(fixture_db),
        "--format", "json",
        "meetings", "transcript", "mtg-001",
        "--limit", "2"
    ])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2


def test_meetings_history_alias(fixture_db):
    """Test meetings history (alias for transcript)."""
    runner = CliRunner()
    result = runner.invoke(main, [
        "--db", str(fixture_db),
        "--format", "json",
        "meetings", "history", "mtg-001"
    ])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 4


def test_meetings_read_alias(fixture_db):
    """Test meetings read (alias for transcript)."""
    runner = CliRunner()
    result = runner.invoke(main, [
        "--db", str(fixture_db),
        "--format", "json",
        "meetings", "read", "mtg-001"
    ])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 4


def test_dictations_list(fixture_db):
    """Test dictations list command."""
    runner = CliRunner()
    result = runner.invoke(main, [
        "--db", str(fixture_db),
        "--format", "json",
        "dictations", "list"
    ])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    assert data[0]["title"] == "Quick note"


def test_dictations_list_with_limit(fixture_db):
    """Test dictations list with limit."""
    runner = CliRunner()
    result = runner.invoke(main, [
        "--db", str(fixture_db),
        "--format", "json",
        "dictations", "list",
        "--limit", "1"
    ])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1


def test_compact_json(fixture_db):
    """Test compact JSON output."""
    runner = CliRunner()
    result = runner.invoke(main, [
        "--db", str(fixture_db),
        "--format", "json",
        "--compact",
        "meetings", "list"
    ])
    
    assert result.exit_code == 0
    # Compact JSON should not have newlines between elements
    assert "\n  " not in result.output


def test_field_selection(fixture_db):
    """Test field selection."""
    runner = CliRunner()
    result = runner.invoke(main, [
        "--db", str(fixture_db),
        "--format", "json",
        "--select", "id,title",
        "meetings", "list"
    ])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "id" in data[0]
    assert "title" in data[0]
    assert "source" not in data[0]


def test_meeting_not_found(fixture_db):
    """Test error handling for non-existent meeting."""
    runner = CliRunner()
    result = runner.invoke(main, [
        "--db", str(fixture_db),
        "meetings", "show", "nonexistent"
    ])
    
    assert result.exit_code == 3  # EXIT_NOT_FOUND


def test_help_command():
    """Test help output."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    
    assert result.exit_code == 0
    assert "walkie" in result.output.lower()
    assert "meeting" in result.output.lower()
