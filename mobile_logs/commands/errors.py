"""Errors command - show sessions containing errors."""

import click
from ..extractor import load_logs
from ..parser import parse_file
from ..filters import get_errors
from ..redactor import redact_entry
from ..datetime_utils import format_time_short
from ..grouping import group_by_sessions, format_session_header, DEFAULT_GAP_THRESHOLD


@click.command()
@click.argument('source', type=click.Path(exists=True))
@click.option('--redact', '-r', is_flag=True, help='Redact sensitive information')
@click.option('--limit', '-n', default=None, type=int, help='Limit number of sessions shown')
@click.option('--gap', '-g', default=DEFAULT_GAP_THRESHOLD, type=float,
              help=f'Session gap threshold in seconds (default: {DEFAULT_GAP_THRESHOLD})')
def errors(source: str, redact: bool, limit: int, gap: float):
    """Show sessions containing errors.
    
    Displays full sessions that contain at least one error entry,
    providing context around each error.
    
    SOURCE can be a zip file or directory containing flog*.txt files.
    
    \b
    Examples:
        cstool logs-errors logs.zip
        cstool logs-errors logs.zip --redact         # redact sensitive data
        cstool logs-errors logs.zip --gap 60         # 1-minute session threshold
        cstool logs-errors logs.zip -n 5             # limit to 5 sessions
    """
    try:
        logs = load_logs(source)
        
        if not logs.log_files:
            click.echo(click.style("❌ No log files found", fg="red"))
            return
        
        # Parse all entries
        all_entries = []
        for log_file in logs.log_files:
            all_entries.extend(parse_file(log_file))
        
        # Sort by timestamp
        all_entries.sort(key=lambda e: e.timestamp)
        
        # Group ALL entries into sessions
        all_sessions = group_by_sessions(all_entries, gap)
        
        # Filter to sessions that contain at least one error
        error_sessions = [s for s in all_sessions if s.error_count > 0]
        
        if not error_sessions:
            click.echo(click.style("✅ No errors found!", fg="green", bold=True))
            logs.cleanup()
            return
        
        # Apply limit
        if limit:
            error_sessions = error_sessions[:limit]
        
        # Count total errors across shown sessions
        total_errors = sum(s.error_count for s in error_sessions)
        
        click.echo()
        click.echo(click.style(
            f"⛔ Found {total_errors} error(s) in {len(error_sessions)} session(s)",
            fg="red", bold=True
        ))
        
        # Display each session with errors
        for session in error_sessions:
            click.echo()
            click.echo(click.style(
                format_session_header(session, 70, show_errors=True),
                fg="red"
            ))
            click.echo()
            
            for entry in session.entries:
                if redact:
                    entry = redact_entry(entry)
                _display_entry(entry)
        
        logs.cleanup()
        
    except Exception as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red"))


def _display_entry(entry):
    """Display a single log entry with appropriate formatting."""
    ts = format_time_short(entry.timestamp)
    module = f"[{entry.module}] " if entry.module else ""
    
    if entry.level == 'error':
        icon = click.style("⛔", fg="red")
        ts_style = click.style(ts, fg="red", bold=True)
        module_style = click.style(module, fg="red")
    else:
        icon = "💡"
        ts_style = click.style(ts, fg="yellow")
        module_style = click.style(module, fg="blue")
    
    # First line of message, truncated
    msg = entry.message.split('\n')[0]
    if len(msg) > 120:
        msg = msg[:120] + "..."
    
    # Highlight error messages
    if entry.level == 'error':
        msg = click.style(msg, fg="red")
    
    click.echo(f"{icon} {ts_style} {module_style}{msg}")
