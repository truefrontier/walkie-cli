"""Pytest configuration and fixtures."""

import json
import sqlite3
from pathlib import Path

import pytest


@pytest.fixture
def fixture_db(tmp_path):
    """Create a fixture SQLite database matching Walkie schema."""
    db_path = tmp_path / "history.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create meetings table
    cursor.execute("""
        CREATE TABLE meetings (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'unknown',
            template_id TEXT NOT NULL DEFAULT 'general',
            started_at INTEGER NOT NULL,
            duration_ms INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'recording',
            audio_path TEXT,
            sections TEXT NOT NULL DEFAULT '[]',
            action_items TEXT NOT NULL DEFAULT '[]',
            user_notes TEXT NOT NULL DEFAULT '',
            has_system_audio INTEGER NOT NULL DEFAULT 0,
            summary_error TEXT,
            folder TEXT,
            participants TEXT NOT NULL DEFAULT '[]',
            roster_hint TEXT,
            title_custom INTEGER NOT NULL DEFAULT 0,
            usage_reported INTEGER NOT NULL DEFAULT 0,
            attendees TEXT NOT NULL DEFAULT '[]',
            continues TEXT,
            speaker_names TEXT NOT NULL DEFAULT '{}',
            call_id TEXT,
            speaker_guesses TEXT NOT NULL DEFAULT '{}',
            company_domain TEXT,
            share_optout INTEGER NOT NULL DEFAULT 0,
            captured_mode TEXT,
            app_roster TEXT NOT NULL DEFAULT '[]',
            app_roster_exact INTEGER NOT NULL DEFAULT 0,
            folder_suggestions TEXT NOT NULL DEFAULT '[]'
        )
    """)
    
    # Create meeting_segments table
    cursor.execute("""
        CREATE TABLE meeting_segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT NOT NULL,
            speaker TEXT NOT NULL,
            start_ms INTEGER NOT NULL,
            end_ms INTEGER NOT NULL,
            text TEXT NOT NULL
        )
    """)
    
    # Create transcription_history table
    cursor.execute("""
        CREATE TABLE transcription_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            saved BOOLEAN NOT NULL DEFAULT 0,
            title TEXT NOT NULL,
            transcription_text TEXT NOT NULL,
            post_processed_text TEXT,
            post_process_prompt TEXT,
            is_agent BOOLEAN NOT NULL DEFAULT 0,
            agent_response TEXT,
            app_bundle_id TEXT,
            app_name TEXT,
            kind TEXT NOT NULL DEFAULT 'dictation',
            agent_session TEXT
        )
    """)
    
    # Insert fixture meetings
    cursor.execute("""
        INSERT INTO meetings (
            id, title, source, started_at, duration_ms, status,
            sections, action_items, participants, attendees
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "mtg-001",
        "Team Standup",
        "zoom",
        1700000000000,  # 2023-11-14 22:13:20
        600000,  # 10 minutes
        "ready",
        json.dumps([{"title": "Updates", "content": "Team updates"}]),
        json.dumps([{"text": "Review PR #123", "assignee": "Alice"}]),
        json.dumps(["you", "them:1"]),
        json.dumps(["Alice", "Bob"])
    ))
    
    cursor.execute("""
        INSERT INTO meetings (
            id, title, source, started_at, duration_ms, status,
            sections, action_items, participants, attendees
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "mtg-002",
        "Design Review",
        "google-meet",
        1700100000000,  # ~27 hours later
        900000,  # 15 minutes
        "ready",
        json.dumps([]),
        json.dumps([]),
        json.dumps(["you"]),
        json.dumps(["Charlie"])
    ))
    
    # Insert fixture segments for mtg-001
    segments = [
        ("mtg-001", "you", 0, 5000, "Good morning everyone!"),
        ("mtg-001", "them:1", 5500, 12000, "Morning! Let's start with updates."),
        ("mtg-001", "you", 12500, 20000, "I finished the authentication module."),
        ("mtg-001", "them:1", 20500, 30000, "Great work! Can you review PR 123?"),
    ]
    cursor.executemany("""
        INSERT INTO meeting_segments (meeting_id, speaker, start_ms, end_ms, text)
        VALUES (?, ?, ?, ?, ?)
    """, segments)
    
    # Insert fixture segments for mtg-002
    segments_002 = [
        ("mtg-002", "you", 0, 8000, "Let's review the new dashboard design."),
        ("mtg-002", "them:1", 8500, 15000, "The color scheme looks good."),
    ]
    cursor.executemany("""
        INSERT INTO meeting_segments (meeting_id, speaker, start_ms, end_ms, text)
        VALUES (?, ?, ?, ?, ?)
    """, segments_002)
    
    # Insert fixture dictations
    dictations = [
        ("walkie-001", 1700000000, "Todo for today", "Finish the CLI implementation", "dictation", "VS Code"),
        ("walkie-002", 1700010000, "Quick note", "Remember to update docs", "dictation", "Slack"),
    ]
    cursor.executemany("""
        INSERT INTO transcription_history (
            file_name, timestamp, title, transcription_text, kind, app_name
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, dictations)
    
    conn.commit()
    conn.close()
    
    return db_path
