"""Export command - export filtered logs to file."""

import click
import json
from pathlib import Path
from ..extractor import load_logs
from ..parser import parse_file
from ..filters import filter_entries
from ..redactor import redact_entries
from ..datetime_utils import parse_datetime_filter, format_datetime_human, format_duration
from ..grouping import group_by_sessions, format_session_header, get_session_stats, DEFAULT_GAP_THRESHOLD


def _resolve_output_path(output: str, source: str, fmt: str) -> Path:
    """
    Resolve the output path.
    
    If output is None, derive from source name with appropriate extension.
    If output is an absolute path, use it as-is.
    If output is a relative path, place it next to the source.
    
    Args:
        output: The output path provided by user (or None for auto)
        source: The source log file/directory path
        fmt: The output format ('json' or 'text')
        
    Returns:
        Resolved Path object
    """
    source_path = Path(source)
    
    # Auto-generate filename if not provided
    if output is None:
        # Use source name with new extension
        ext = '.json' if fmt == 'json' else '.txt'
        base_name = source_path.stem if source_path.is_file() else source_path.name
        output_name = base_name + ext
        
        # Place next to source
        if source_path.is_file():
            return source_path.parent / output_name
        else:
            return source_path / output_name
    
    output_path = Path(output)
    
    # If it's an absolute path, use it directly
    if output_path.is_absolute():
        return output_path
    
    # Otherwise, resolve relative to the source location
    if source_path.is_file():
        return source_path.parent / output_path
    else:
        return source_path / output_path


@click.command()
@click.argument('source', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), default=None,
              help='Output file path (default: <source_name>.json or .txt)')
@click.option('--module', '-m', help='Filter by module name')
@click.option('--level', '-l', type=click.Choice(['info', 'error']), help='Filter by log level')
@click.option('--search', '-s', help='Filter by text search')
@click.option('--after', '-a', help='Only entries after this time (flexible: 2026-01-15, jan 15, 01-15 10:30)')
@click.option('--before', '-b', help='Only entries before this time (flexible formats supported)')
@click.option('--redact', '-r', is_flag=True, help='Redact sensitive information (emails, UUIDs, tokens)')
@click.option('--format', '-f', 'fmt', type=click.Choice(['text', 'json']), default='json', help='Output format (default: json)')
@click.option('--group/--no-group', default=True, help='Group entries by session in output (default: enabled)')
@click.option('--gap', '-g', default=DEFAULT_GAP_THRESHOLD, type=float,
              help=f'Session gap threshold in seconds (default: {DEFAULT_GAP_THRESHOLD})')
def export(source: str, output: str, module: str, level: str, search: str, after: str, 
           before: str, redact: bool, fmt: str, group: bool, gap: float):
    """Export log entries to a file.
    
    SOURCE can be a zip file or directory containing flog*.txt files.
    
    By default, exports to <source_name>.json next to the source.
    Use -o to specify a custom output path.
    
    \b
    Date/time formats supported for --after and --before:
      2026-01-15          Full ISO date
      2026-01-15 10:30    ISO date with time
      01-15 or 1/15       Month-day (assumes current year)
      jan 15              Named month
      jan 15 10pm         Named month with time
    
    \b
    Examples:
        cstool logs-export logs.zip                        # exports to logs.json
        cstool logs-export logs.zip -f text                # exports to logs.txt
        cstool logs-export logs.zip -o custom.json         # custom filename
        cstool logs-export logs.zip -l error               # only errors
        cstool logs-export logs.zip -a "jan 15" -b "jan 16"
        cstool logs-export logs.zip --redact               # redact sensitive data
        cstool logs-export logs.zip --no-group             # disable session grouping
    """
    try:
        logs = load_logs(source)
        
        if not logs.log_files:
            click.echo(click.style("❌ No log files found", fg="red"))
            return
        
        # Resolve output path (auto-generate if not provided)
        output_path = _resolve_output_path(output, source, fmt)
        
        # Parse all entries
        all_entries = []
        for log_file in logs.log_files:
            all_entries.extend(parse_file(log_file))
        
        # Sort by timestamp
        all_entries.sort(key=lambda e: e.timestamp)
        
        # Parse time filters using flexible parser
        after_dt = None
        before_dt = None
        
        if after:
            try:
                after_dt = parse_datetime_filter(after, 'after')
            except ValueError as e:
                click.echo(click.style(f"❌ Invalid --after value: {e}", fg="red"))
                logs.cleanup()
                return
        
        if before:
            try:
                before_dt = parse_datetime_filter(before, 'before')
            except ValueError as e:
                click.echo(click.style(f"❌ Invalid --before value: {e}", fg="red"))
                logs.cleanup()
                return
        
        # Apply filters
        results = filter_entries(
            all_entries,
            level=level,
            module=module,
            search=search,
            after=after_dt,
            before=before_dt
        )
        
        if not results:
            click.echo(click.style("No matching entries to export.", fg="yellow"))
            logs.cleanup()
            return
        
        # Redact if requested
        if redact:
            results = redact_entries(results)
        
        # Export
        if fmt == 'json':
            _export_json(results, output_path, group, gap)
        else:
            _export_text(results, output_path, group, gap)
        
        click.echo(click.style(f"✅ Exported {len(results)} entries to {output_path}", fg="green", bold=True))
        if redact:
            click.echo(click.style("   (sensitive data redacted)", fg="yellow"))
        if group:
            sessions = group_by_sessions(results, gap)
            if len(sessions) > 1:
                click.echo(click.style(f"   ({len(sessions)} sessions detected)", fg="cyan"))
        
        logs.cleanup()
        
    except Exception as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red"))


def _export_text(entries: list, output_path: Path, group: bool, gap_threshold: float):
    """Export entries as text, optionally grouped by session."""
    with open(output_path, 'w', encoding='utf-8') as f:
        if group:
            sessions = group_by_sessions(entries, gap_threshold)
            
            for session in sessions:
                # Write session header if multiple sessions
                if len(sessions) > 1:
                    f.write("\n")
                    f.write(format_session_header(session, 70) + "\n")
                    f.write("\n")
                
                for entry in session.entries:
                    _write_entry_text(f, entry)
        else:
            for entry in entries:
                _write_entry_text(f, entry)


def _write_entry_text(f, entry):
    """Write a single entry in text format."""
    ts = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    module = f"[{entry.module}] " if entry.module else ""
    icon = "⛔" if entry.level == 'error' else "💡"
    
    f.write(f"{icon} [{ts}] {module}{entry.message}\n")
    f.write("-" * 60 + "\n")


def _export_json(entries: list, output_path: Path, group: bool, gap_threshold: float):
    """Export entries as JSON, optionally with session metadata."""
    if group:
        sessions = group_by_sessions(entries, gap_threshold)
        
        data = {
            'sessions': [],
            'stats': get_session_stats(sessions)
        }
        
        for session in sessions:
            session_data = {
                'session_number': session.index,
                'start_time': session.start_time.isoformat() if session.start_time else None,
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'duration_seconds': session.duration_seconds,
                'entry_count': session.entry_count,
                'error_count': session.error_count,
                'entries': [_entry_to_dict(e) for e in session.entries]
            }
            data['sessions'].append(session_data)
    else:
        data = {
            'entries': [_entry_to_dict(e) for e in entries]
        }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def _entry_to_dict(entry) -> dict:
    """Convert a log entry to a dictionary."""
    return {
        'timestamp': entry.timestamp.isoformat(),
        'level': entry.level,
        'module': entry.module,
        'message': entry.message,
        'file': entry.file_source,
        'line': entry.line_number
    }
