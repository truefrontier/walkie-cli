"""Agent-native UX utilities for walkie-cli."""

import csv
import json
import sys
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table


EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NOT_FOUND = 3
EXIT_MISSING_DB = 4
EXIT_RUNTIME = 5


def is_tty() -> bool:
    """Check if stdout is a TTY."""
    return sys.stdout.isatty()


def output_data(
    data: Any,
    format: Optional[str] = None,
    compact: bool = False,
    select: Optional[str] = None,
    csv_output: bool = False,
    quiet: bool = False,
) -> None:
    """Output data in the appropriate format for agents or humans.
    
    Args:
        data: Data to output (dict, list, or primitive)
        format: 'table', 'json', or None (auto-detect based on TTY)
        compact: Use compact JSON formatting
        select: Comma-separated list of fields to include
        csv_output: Output in CSV format
        quiet: Suppress all output
    """
    if quiet:
        return

    if data is None:
        return

    # Apply field selection if requested
    if select:
        fields = [f.strip() for f in select.split(",")]
        data = _select_fields(data, fields)

    # Auto-detect format
    if format is None:
        format = "table" if is_tty() else "json"

    # CSV output
    if csv_output:
        _output_csv(data)
        return

    # JSON output
    if format == "json":
        indent = None if compact else 2
        json.dump(data, sys.stdout, indent=indent, default=str)
        if not compact:
            print()
        return

    # Table output (human-readable)
    if format == "table":
        _output_table(data)
        return


def _select_fields(data: Any, fields: List[str]) -> Any:
    """Select specific fields from data."""
    if isinstance(data, dict):
        return {k: v for k, v in data.items() if k in fields}
    elif isinstance(data, list):
        return [_select_fields(item, fields) for item in data]
    return data


def _output_csv(data: Any) -> None:
    """Output data as CSV."""
    if not data:
        return

    # Single dict
    if isinstance(data, dict):
        data = [data]

    # List of dicts
    if isinstance(data, list) and data and isinstance(data[0], dict):
        fieldnames = list(data[0].keys())
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            # Convert complex types to strings
            clean_row = {k: _csv_safe(v) for k, v in row.items()}
            writer.writerow(clean_row)
    else:
        # Fallback: just write raw values
        writer = csv.writer(sys.stdout)
        if isinstance(data, list):
            for item in data:
                writer.writerow([_csv_safe(item)])
        else:
            writer.writerow([_csv_safe(data)])


def _csv_safe(value: Any) -> str:
    """Convert value to CSV-safe string."""
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)
    return str(value)


def _output_table(data: Any) -> None:
    """Output data as a rich table."""
    console = Console()

    # Single dict: vertical key-value table
    if isinstance(data, dict):
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value")
        for key, value in data.items():
            table.add_row(str(key), _format_value(value))
        console.print(table)
        return

    # List of dicts: horizontal table
    if isinstance(data, list) and data:
        if isinstance(data[0], dict):
            table = Table()
            headers = list(data[0].keys())
            for header in headers:
                table.add_column(header, style="cyan" if header in ["id", "meeting_id"] else None)
            for row in data:
                table.add_row(*[_format_value(row.get(h)) for h in headers])
            console.print(table)
            return

        # List of primitives
        for item in data:
            console.print(_format_value(item))
        return

    # Primitive value
    console.print(_format_value(data))


def _format_value(value: Any, max_len: int = 100) -> str:
    """Format a value for table display."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "✓" if value else ""
    if isinstance(value, (dict, list)):
        s = json.dumps(value, default=str)
        if len(s) > max_len:
            return s[:max_len - 3] + "..."
        return s
    s = str(value)
    if len(s) > max_len:
        return s[:max_len - 3] + "..."
    return s


def error(message: str, exit_code: int = EXIT_RUNTIME) -> None:
    """Print error message to stderr and exit."""
    console = Console(stderr=True)
    console.print(f"[bold red]Error:[/bold red] {message}")
    sys.exit(exit_code)
