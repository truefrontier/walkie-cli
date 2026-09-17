# walkie-cli Installation Guide for Kevin's Mac

## Package Information

- **Version**: 0.1.0
- **Artifact**: `walkie-cli-0.1.0.zip`
- **SHA256**: `bd88ac83befacaf4944fe479bb2307a0ba49f823301fe1329a027257bc3d603e`
- **Git Commit**: `2b2a89282f9bb5b6d5e2c2bb2dd2f5ec79461afa`

## Installation from Zip Archive

Since Origin git HTTPS isn't authenticated from the install host, use the packaged zip:

### Step 1: Download the artifact

```bash
# From the cloud agent VM or wherever you have access
scp /workspace/artifacts/walkie-cli-0.1.0.zip kevin@mac:/tmp/
```

Or clone the repo and extract the artifact:

```bash
# If you have access to the Origin repo
git clone https://origin.cursor.com/kevnk/tmp-5b2444c3da1660db.git
cd tmp-5b2444c3da1660db
# The artifact is at: artifacts/walkie-cli-0.1.0.zip
```

### Step 2: Install on Mac

```bash
# Verify the download
sha256sum /tmp/walkie-cli-0.1.0.zip
# Should match: bd88ac83befacaf4944fe479bb2307a0ba49f823301fe1329a027257bc3d603e

# Extract
cd /tmp
unzip walkie-cli-0.1.0.zip -d walkie-cli-source

# Install via pipx (recommended)
cd walkie-cli-source
pipx install .

# Or via pip
pip install .
```

### Step 3: Verify installation

```bash
walkie --version
# Should show: walkie, version 0.1.0

walkie --help
```

## Quick Smoke Test (if Walkie.app has data)

```bash
# Check database status
walkie status

# List recent meetings
walkie meetings list --limit 5

# Get a meeting by title substring
walkie meetings show "standup"

# View transcript
walkie meetings transcript mtg-<your-meeting-id>

# JSON output for agents
walkie --format json meetings list
```

## Database Location

walkie-cli auto-discovers the Walkie.app database at:

```
~/Library/Application Support/com.pais.walkie/accounts/<accountId>/history.db
```

Or specify explicitly:

```bash
walkie --db ~/Library/Application\ Support/com.pais.walkie/accounts/<accountId>/history.db status
```

## Schema Verification

The CLI matches the live Walkie.app v1.13.1 schema verified from Kevin's Mac:

### Tables & Columns

**meetings**: id, title, source, template_id, started_at, duration_ms, status, audio_path, sections, action_items, user_notes, has_system_audio, summary_error, folder, participants, roster_hint, title_custom, usage_reported, attendees, continues, speaker_names, call_id, speaker_guesses, company_domain, share_optout, captured_mode, app_roster, app_roster_exact, folder_suggestions

**meeting_segments**: id, meeting_id, speaker, start_ms, end_ms, text

**transcription_history**: id, file_name, timestamp, saved, title, transcription_text, post_processed_text, post_process_prompt, is_agent, agent_response, app_bundle_id, app_name, kind, agent_session

## Safety

✅ Read-only SQLite access (`mode=ro`)  
✅ No write/send/delete commands  
✅ No network calls  
✅ All data stays on your Mac  

## Support

- Repository: https://origin.cursor.com/kevnk/tmp-5b2444c3da1660db
- License: MIT (True Frontier)
- Tests: 27/27 passing
