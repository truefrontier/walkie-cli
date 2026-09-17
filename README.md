# walkie-cli

**Read-only CLI for Walkie.app meeting transcripts and dictations**

`walkie-cli` is an agent-native, read-only command-line interface for accessing meeting transcripts and dictations from the local [Walkie.app](https://walkie.app/) (macOS) SQLite database. All data stays on your Mac—no network access, no authentication, no cloud APIs.

## Features

- 🔒 **Read-only**: Never writes to the Walkie database
- 🤖 **Agent-native**: Auto-JSON output for AI agents, rich tables for humans
- 📊 **Multiple formats**: Table, JSON, CSV output
- 🔍 **Smart search**: Find meetings by ID or title substring
- 🎯 **Zero dependencies**: Uses only local SQLite database
- 🚫 **Privacy-first**: No network calls, no cookies, no telemetry

## Installation

### From Origin (recommended for True Frontier team)

```bash
pipx install git+https://origin.cursor.sh/truefrontier/walkie-cli.git
```

### From PyPI (when published)

```bash
pipx install walkie-cli
```

### For development

```bash
git clone https://origin.cursor.sh/truefrontier/walkie-cli.git
cd walkie-cli
pip install -e .
```

## Quick Start

```bash
# Check database status
walkie status

# List recent meetings
walkie meetings list

# Show a specific meeting
walkie meetings show "standup"

# Read full transcript
walkie meetings transcript mtg-1234567890

# List recent dictations
walkie dictations list
```

## Commands

### Global Options

All commands support these flags:

- `--db PATH` — Explicit path to `history.db` (overrides auto-discovery)
- `--account ID` — Account ID when multiple Walkie accounts exist
- `--format table|json` — Output format (default: auto-detect from TTY)
- `--compact` — Compact JSON (no indentation)
- `--select FIELDS` — Comma-separated field list to include
- `--csv` — CSV output
- `-q, --quiet` — Suppress all output

### `walkie status`

Show database path, account ID, and record counts.

```bash
walkie status
```

**Example output:**

```
Key                 Value
db_path             /Users/you/Library/Application Support/com.pais.walkie/accounts/abc123/history.db
account_id          abc123
meeting_count       42
segment_count       1337
dictation_count     89
```

### `walkie meetings list`

List recent meetings with summary info.

```bash
walkie meetings list [--limit N]
```

**Options:**

- `--limit N` — Show only N most recent meetings

**Example:**

```bash
walkie meetings list --limit 5
```

### `walkie meetings show|get <id-or-title>`

Show detailed metadata for a specific meeting. Accepts meeting ID or title substring.

```bash
walkie meetings show mtg-1234567890
walkie meetings get "standup"
```

**Output includes:**

- Meeting metadata (title, source, timestamps, duration, status)
- Parsed sections (if present)
- Action items (if present)
- Participants and attendees
- Segment count

### `walkie meetings transcript|history|read <id-or-title>`

Display the full meeting transcript as chronological segments.

```bash
walkie meetings transcript mtg-1234567890
walkie meetings history "standup"
walkie meetings read "design review" --limit 10
```

**Options:**

- `--limit N` — Show only first N segments

**Aliases:** `transcript`, `history`, `read`

### `walkie dictations list`

List recent dictations from transcription history.

```bash
walkie dictations list [--limit N]
```

## Database Discovery

`walkie-cli` finds your Walkie database automatically:

1. **Explicit path**: `--db /path/to/history.db` or env `WALKIE_DB`
2. **Default location**: `~/Library/Application Support/com.pais.walkie/accounts/<accountId>/history.db`
3. **Multiple accounts**: Uses the only account, or the newest by modification time
4. **Specific account**: `--account <accountId>` to pick a specific account

## Agent-Native UX

`walkie-cli` follows agent-native conventions from `printing-press`, `limsg`, and `keep`:

- **Auto-format**: JSON for pipes/scripts, rich tables for humans
- **Exit codes**:
  - `0` — Success
  - `2` — Usage error
  - `3` — Not found (meeting/dictation)
  - `4` — Database missing/inaccessible
  - `5` — Runtime error
- **Field selection**: `--select id,title,started` to trim output
- **Quiet mode**: `-q` for side-effect-only commands

### Examples for AI Agents

```bash
# Get meeting as JSON
walkie meetings show "standup" --format json --compact

# Count meetings
walkie meetings list --format json | jq 'length'

# Extract action items
walkie meetings show "standup" --format json | jq '.action_items'

# Get transcript text only
walkie meetings transcript "sync" --select text --csv
```

## Privacy & Safety

- ✅ **Read-only**: Opens database with `mode=ro` flag
- ✅ **No writes**: Never runs `UPDATE`, `INSERT`, or `DELETE`
- ✅ **No network**: Zero network calls
- ✅ **No secrets**: Does not read Walkie auth/settings stores
- ⚠️ **Privacy warning**: Transcripts stay on your Mac—be mindful when pasting meeting text into cloud AI chats

## Database Schema Notes

Based on Walkie.app v1.13.1 schema:

- **Meetings**: Stored in `meetings` table with metadata (title, source, timestamps, template)
- **Segments**: Individual speaker turns in `meeting_segments` (speaker, timestamps, text)
- **Dictations**: Standalone transcriptions in `transcription_history` (kind='dictation')
- **Timestamps**: Stored as millisecond epochs; formatted to ISO 8601 in output
- **JSON fields**: `sections`, `action_items`, `participants`, `attendees` stored as JSON strings

### Schema Quirks

- `started_at` is millisecond epoch, `transcription_history.timestamp` is second epoch
- Speaker labels: `you` (user), `them:N` (other participants)
- Audio files: Stored at `accounts/<accountId>/meetings/<meetingId>/meeting.wav`
- Multiple accounts: Tracked via directory structure, not in database

## Requirements

- macOS (Walkie.app support)
- Python ≥3.8
- Walkie.app installed with at least one account

## Development

```bash
# Clone
git clone https://origin.cursor.sh/truefrontier/walkie-cli.git
cd walkie-cli

# Install in editable mode
pip install -e .

# Run tests
python -m pytest tests/

# Type check
mypy walkie_cli
```

## License

MIT License — Copyright (c) 2026 True Frontier

See [LICENSE](LICENSE) for full text.

## Contributing

Issues and pull requests welcome! This is a read-only tool by design—we will not accept PRs that add write/mutate operations.

## Credits

Built for True Frontier by Kevin.

Inspired by agent-native CLIs: `printing-press`, `limsg`, `keep`.
