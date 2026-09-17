"""Database access layer for Walkie.app SQLite databases."""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import agent_ux


DEFAULT_WALKIE_ROOT = Path.home() / "Library" / "Application Support" / "com.pais.walkie"


class WalkieDB:
    """Read-only access to Walkie.app database."""

    def __init__(self, db_path: Optional[Path] = None, account_id: Optional[str] = None):
        """Initialize database connection.
        
        Args:
            db_path: Explicit path to history.db (overrides discovery)
            account_id: Account ID to use (if multiple accounts exist)
        """
        self.db_path = self._resolve_db_path(db_path, account_id)
        self.account_id = self._extract_account_id(self.db_path)
        self.conn = self._connect()

    def _resolve_db_path(self, explicit_path: Optional[Path], account_id: Optional[str]) -> Path:
        """Resolve the database path."""
        # 1. Explicit path via --db or WALKIE_DB
        if explicit_path:
            if not explicit_path.exists():
                agent_ux.error(f"Database not found: {explicit_path}", agent_ux.EXIT_MISSING_DB)
            return explicit_path

        # 2. WALKIE_DB environment variable
        env_path = os.environ.get("WALKIE_DB")
        if env_path:
            p = Path(env_path).expanduser()
            if not p.exists():
                agent_ux.error(f"WALKIE_DB database not found: {p}", agent_ux.EXIT_MISSING_DB)
            return p

        # 3. Discover from default Walkie root
        walkie_root = DEFAULT_WALKIE_ROOT
        if not walkie_root.exists():
            agent_ux.error(
                f"Walkie.app directory not found: {walkie_root}\n"
                "Set WALKIE_DB or use --db PATH to specify database location.",
                agent_ux.EXIT_MISSING_DB
            )

        accounts_dir = walkie_root / "accounts"
        if not accounts_dir.exists():
            agent_ux.error(
                f"No accounts directory found in {walkie_root}",
                agent_ux.EXIT_MISSING_DB
            )

        # List all account directories
        account_dirs = [d for d in accounts_dir.iterdir() if d.is_dir()]
        if not account_dirs:
            agent_ux.error(
                f"No account directories found in {accounts_dir}",
                agent_ux.EXIT_MISSING_DB
            )

        # Filter by account_id if specified
        if account_id:
            matching = [d for d in account_dirs if d.name == account_id]
            if not matching:
                agent_ux.error(
                    f"Account '{account_id}' not found in {accounts_dir}",
                    agent_ux.EXIT_NOT_FOUND
                )
            target_dir = matching[0]
        elif len(account_dirs) == 1:
            target_dir = account_dirs[0]
        else:
            # Multiple accounts: pick newest by mtime
            target_dir = max(account_dirs, key=lambda d: d.stat().st_mtime)

        db_path = target_dir / "history.db"
        if not db_path.exists():
            agent_ux.error(
                f"Database not found at {db_path}",
                agent_ux.EXIT_MISSING_DB
            )

        return db_path

    def _extract_account_id(self, db_path: Path) -> str:
        """Extract account ID from database path."""
        # Path structure: .../accounts/<accountId>/history.db
        parts = db_path.parts
        try:
            accounts_idx = parts.index("accounts")
            return parts[accounts_idx + 1]
        except (ValueError, IndexError):
            return "unknown"

    def _connect(self) -> sqlite3.Connection:
        """Connect to database in read-only mode."""
        uri = f"file:{self.db_path}?mode=ro"
        try:
            conn = sqlite3.connect(uri, uri=True)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            agent_ux.error(f"Failed to open database: {e}", agent_ux.EXIT_RUNTIME)

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def get_status(self) -> Dict[str, Any]:
        """Get database status information."""
        cursor = self.conn.cursor()
        
        # Count meetings
        cursor.execute("SELECT COUNT(*) FROM meetings")
        meeting_count = cursor.fetchone()[0]
        
        # Count segments
        cursor.execute("SELECT COUNT(*) FROM meeting_segments")
        segment_count = cursor.fetchone()[0]
        
        # Count dictations
        cursor.execute("SELECT COUNT(*) FROM transcription_history WHERE kind = 'dictation'")
        dictation_count = cursor.fetchone()[0]
        
        return {
            "db_path": str(self.db_path),
            "account_id": self.account_id,
            "meeting_count": meeting_count,
            "segment_count": segment_count,
            "dictation_count": dictation_count,
        }

    def list_meetings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List meetings ordered by most recent first.
        
        Args:
            limit: Maximum number of meetings to return
        """
        query = """
            SELECT 
                m.id,
                m.title,
                m.source,
                m.started_at,
                m.duration_ms,
                m.status,
                m.folder,
                COUNT(s.id) as segment_count
            FROM meetings m
            LEFT JOIN meeting_segments s ON m.id = s.meeting_id
            GROUP BY m.id
            ORDER BY m.started_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.conn.cursor()
        cursor.execute(query)
        
        meetings = []
        for row in cursor.fetchall():
            meetings.append({
                "id": row["id"],
                "title": row["title"],
                "source": row["source"],
                "started": self._format_timestamp(row["started_at"]),
                "duration": self._format_duration(row["duration_ms"]),
                "status": row["status"],
                "folder": row["folder"] or "",
                "segment_count": row["segment_count"],
            })
        
        return meetings

    def get_meeting(self, id_or_substr: str) -> Optional[Dict[str, Any]]:
        """Get meeting by ID or title substring.
        
        Args:
            id_or_substr: Meeting ID or substring of title
        """
        cursor = self.conn.cursor()
        
        # Try exact ID match first
        cursor.execute("SELECT * FROM meetings WHERE id = ?", (id_or_substr,))
        row = cursor.fetchone()
        
        # Try title substring match
        if not row:
            cursor.execute(
                "SELECT * FROM meetings WHERE title LIKE ? ORDER BY started_at DESC LIMIT 1",
                (f"%{id_or_substr}%",)
            )
            row = cursor.fetchone()
        
        if not row:
            return None
        
        # Get segment count
        cursor.execute("SELECT COUNT(*) FROM meeting_segments WHERE meeting_id = ?", (row["id"],))
        segment_count = cursor.fetchone()[0]
        
        return {
            "id": row["id"],
            "title": row["title"],
            "source": row["source"],
            "template_id": row["template_id"],
            "started": self._format_timestamp(row["started_at"]),
            "started_at": row["started_at"],
            "duration": self._format_duration(row["duration_ms"]),
            "duration_ms": row["duration_ms"],
            "status": row["status"],
            "audio_path": row["audio_path"] or "",
            "folder": row["folder"] or "",
            "user_notes": row["user_notes"] or "",
            "sections": self._parse_json(row["sections"]),
            "action_items": self._parse_json(row["action_items"]),
            "participants": self._parse_json(row["participants"]),
            "attendees": self._parse_json(row["attendees"]),
            "segment_count": segment_count,
            "has_system_audio": bool(row["has_system_audio"]),
        }

    def get_meeting_transcript(self, id_or_substr: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get meeting transcript (segments) by ID or title substring.
        
        Args:
            id_or_substr: Meeting ID or substring of title
            limit: Maximum number of segments to return
        """
        # First, resolve the meeting ID
        meeting = self.get_meeting(id_or_substr)
        if not meeting:
            return []
        
        meeting_id = meeting["id"]
        
        query = """
            SELECT speaker, start_ms, end_ms, text
            FROM meeting_segments
            WHERE meeting_id = ?
            ORDER BY start_ms ASC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.conn.cursor()
        cursor.execute(query, (meeting_id,))
        
        segments = []
        for row in cursor.fetchall():
            segments.append({
                "time": self._format_duration(row["start_ms"]),
                "speaker": row["speaker"],
                "text": row["text"],
            })
        
        return segments

    def list_dictations(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List recent dictations from transcription_history.
        
        Args:
            limit: Maximum number of dictations to return
        """
        query = """
            SELECT id, title, timestamp, transcription_text, app_name, app_bundle_id
            FROM transcription_history
            WHERE kind = 'dictation'
            ORDER BY timestamp DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.conn.cursor()
        cursor.execute(query)
        
        dictations = []
        for row in cursor.fetchall():
            dictations.append({
                "id": row["id"],
                "title": row["title"],
                "timestamp": self._format_timestamp(row["timestamp"] * 1000),
                "app": row["app_name"] or row["app_bundle_id"] or "",
                "text": row["transcription_text"],
            })
        
        return dictations

    def _parse_json(self, json_str: str) -> Any:
        """Parse JSON string safely."""
        if not json_str:
            return []
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return []

    def _format_timestamp(self, ms_epoch: int) -> str:
        """Format millisecond epoch timestamp to ISO format."""
        return datetime.fromtimestamp(ms_epoch / 1000).isoformat()

    def _format_duration(self, duration_ms: int) -> str:
        """Format duration in milliseconds to human-readable string."""
        seconds = duration_ms / 1000
        if seconds < 60:
            return f"{seconds:.0f}s"
        minutes = seconds / 60
        if minutes < 60:
            return f"{minutes:.1f}m"
        hours = minutes / 60
        return f"{hours:.1f}h"
