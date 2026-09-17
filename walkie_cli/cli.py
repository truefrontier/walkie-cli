"""CLI interface for walkie-cli."""

import sys
from pathlib import Path
from typing import Optional

import click

from . import __version__, agent_ux
from .db import WalkieDB


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__)
@click.option("--db", type=click.Path(exists=True, path_type=Path), help="Path to history.db")
@click.option("--account", help="Account ID to use (if multiple accounts)")
@click.option("--format", type=click.Choice(["table", "json"]), help="Output format")
@click.option("--compact", is_flag=True, help="Compact JSON output")
@click.option("--select", help="Comma-separated fields to include")
@click.option("--csv", "csv_output", is_flag=True, help="CSV output")
@click.option("-q", "--quiet", is_flag=True, help="Suppress output")
@click.pass_context
def main(ctx, db, account, format, compact, select, csv_output, quiet):
    """walkie: Read-only CLI for Walkie.app meeting transcripts.
    
    Access your local Walkie.app meeting transcripts and dictations without
    network access. All data stays on your Mac.
    
    Global options must be specified before the subcommand:
    
        walkie --db /path/to/db --format json meetings list
    """
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = db
    ctx.obj["account_id"] = account
    ctx.obj["format"] = format
    ctx.obj["compact"] = compact
    ctx.obj["select"] = select
    ctx.obj["csv_output"] = csv_output
    ctx.obj["quiet"] = quiet


@main.command()
@click.pass_context
def status(ctx):
    """Show database status and statistics."""
    db = WalkieDB(ctx.obj["db_path"], ctx.obj["account_id"])
    try:
        status_info = db.get_status()
        agent_ux.output_data(
            status_info,
            format=ctx.obj["format"],
            compact=ctx.obj["compact"],
            select=ctx.obj["select"],
            csv_output=ctx.obj["csv_output"],
            quiet=ctx.obj["quiet"],
        )
    finally:
        db.close()


@main.group()
def meetings():
    """Manage and view meetings."""
    pass


@meetings.command("list")
@click.option("--limit", type=int, help="Maximum number of meetings to show")
@click.pass_context
def meetings_list(ctx, limit):
    """List recent meetings."""
    db = WalkieDB(ctx.obj["db_path"], ctx.obj["account_id"])
    try:
        meetings = db.list_meetings(limit)
        agent_ux.output_data(
            meetings,
            format=ctx.obj["format"],
            compact=ctx.obj["compact"],
            select=ctx.obj["select"],
            csv_output=ctx.obj["csv_output"],
            quiet=ctx.obj["quiet"],
        )
    finally:
        db.close()


@meetings.command("show")
@click.argument("meeting_id")
@click.pass_context
def meetings_show(ctx, meeting_id):
    """Show meeting details by ID or title substring."""
    db = WalkieDB(ctx.obj["db_path"], ctx.obj["account_id"])
    try:
        meeting = db.get_meeting(meeting_id)
        if not meeting:
            agent_ux.error(
                f"Meeting not found: {meeting_id}",
                agent_ux.EXIT_NOT_FOUND
            )
        agent_ux.output_data(
            meeting,
            format=ctx.obj["format"],
            compact=ctx.obj["compact"],
            select=ctx.obj["select"],
            csv_output=ctx.obj["csv_output"],
            quiet=ctx.obj["quiet"],
        )
    finally:
        db.close()


@meetings.command("get")
@click.argument("meeting_id")
@click.pass_context
def meetings_get(ctx, meeting_id):
    """Get meeting details (alias for show)."""
    ctx.invoke(meetings_show, meeting_id=meeting_id)


@meetings.command("transcript")
@click.argument("meeting_id")
@click.option("--limit", type=int, help="Maximum number of segments to show")
@click.pass_context
def meetings_transcript(ctx, meeting_id, limit):
    """Show meeting transcript (chronological segments)."""
    db = WalkieDB(ctx.obj["db_path"], ctx.obj["account_id"])
    try:
        transcript = db.get_meeting_transcript(meeting_id, limit)
        if not transcript:
            agent_ux.error(
                f"Meeting or transcript not found: {meeting_id}",
                agent_ux.EXIT_NOT_FOUND
            )
        agent_ux.output_data(
            transcript,
            format=ctx.obj["format"],
            compact=ctx.obj["compact"],
            select=ctx.obj["select"],
            csv_output=ctx.obj["csv_output"],
            quiet=ctx.obj["quiet"],
        )
    finally:
        db.close()


@meetings.command("history")
@click.argument("meeting_id")
@click.option("--limit", type=int, help="Maximum number of segments to show")
@click.pass_context
def meetings_history(ctx, meeting_id, limit):
    """Show meeting transcript (alias for transcript)."""
    ctx.invoke(meetings_transcript, meeting_id=meeting_id, limit=limit)


@meetings.command("read")
@click.argument("meeting_id")
@click.option("--limit", type=int, help="Maximum number of segments to show")
@click.pass_context
def meetings_read(ctx, meeting_id, limit):
    """Show meeting transcript (alias for transcript)."""
    ctx.invoke(meetings_transcript, meeting_id=meeting_id, limit=limit)


@main.group()
def dictations():
    """View dictation history."""
    pass


@dictations.command("list")
@click.option("--limit", type=int, help="Maximum number of dictations to show")
@click.pass_context
def dictations_list(ctx, limit):
    """List recent dictations."""
    db = WalkieDB(ctx.obj["db_path"], ctx.obj["account_id"])
    try:
        dicts = db.list_dictations(limit)
        agent_ux.output_data(
            dicts,
            format=ctx.obj["format"],
            compact=ctx.obj["compact"],
            select=ctx.obj["select"],
            csv_output=ctx.obj["csv_output"],
            quiet=ctx.obj["quiet"],
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
