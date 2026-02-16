"""Search command - search logs by text, module, or time."""

import click
from ..extractor import load_logs
from ..parser import parse_file
from ..filters import filter_entries
from ..redactor import redact_entry
from ..datetime_utils import parse_datetime_filter, format_time_short
from ..grouping import group_by_sessions, format_session_header, DEFAULT_GAP_THRESHOLD


@click.command()
@click.argument('source', type=click.Path(exists=True))
@click.argument('query', required=False)
@click.option('--module', '-m', help='Filter by module name')
@click.option('--level', '-l', type=click.Choice(['info', 'error']), help='Filter by log level')
@click.option('--after', '-a', help='Only entries after this time (flexible: 2026-01-15, jan 15, 01-15 10:30)')
@click.option('--before', '-b', help='Only entries before this time (flexible formats supported)')
@click.option('--redact', '-r', is_flag=True, help='Redact sensitive information')
@click.option('--limit', '-n', default=50, help='Max results to show (default 50)')
@click.option('--group/--no-group', default=True, help='Group results by session (default: enabled)')
@click.option('--gap', '-g', default=DEFAULT_GAP_THRESHOLD, type=float, 
              help=f'Session gap threshold in seconds (default: {DEFAULT_GAP_THRESHOLD})')
def search(source: str, query: str, module: str, level: str, after: str, before: str, 
           redact: bool, limit: int, group: bool, gap: float):
    """Search log entries.
    
    SOURCE can be a zip file or directory containing flog*.txt files.
    
    QUERY is optional text to search for in log messages.
    
    \b
    Date/time formats supported for --after and --before:
      2026-01-15          Full ISO date
      2026-01-15 10:30    ISO date with time
      01-15 or 1/15       Month-day (assumes current year)
      jan 15              Named month
      jan 15 10pm         Named month with time
    
    \b
    Examples:
        cstool logs-search logs.zip "token"
        cstool logs-search logs.zip -m AuthBloc
        cstool logs-search logs.zip -l error
        cstool logs-search logs.zip -a "jan 15" -b "jan 16"
        cstool logs-search logs.zip -a "jan 15 10am" -b "jan 15 2pm"
        cstool logs-search logs.zip --no-group    # disable session grouping
        cstool logs-search logs.zip --gap 60      # 1-minute session threshold
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
            search=query,
            after=after_dt,
            before=before_dt
        )
        
        total_matches = len(results)
        results = results[:limit]
        
        if not results:
            click.echo(click.style("No matching entries found.", fg="yellow"))
            logs.cleanup()
            return
        
        # Display results
        click.echo(click.style(f"\n🔍 Found {total_matches} matches", fg="cyan", bold=True))
        if total_matches > limit:
            click.echo(click.style(f"   (showing first {limit})", fg="cyan"))
        
        if group:
            _display_grouped(results, redact, gap)
        else:
            click.echo(click.style("─" * 60, fg="cyan"))
            for entry in results:
                if redact:
                    entry = redact_entry(entry)
                _display_entry(entry)
        
        logs.cleanup()
        
    except Exception as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red"))


def _display_grouped(entries: list, redact: bool, gap_threshold: float):
    """Display entries grouped by session."""
    sessions = group_by_sessions(entries, gap_threshold)
    
    for session in sessions:
        # Show session header if multiple sessions
        if len(sessions) > 1:
            click.echo()
            click.echo(click.style(format_session_header(session, 70), fg="cyan"))
        else:
            click.echo(click.style("─" * 70, fg="cyan"))
        
        for entry in session.entries:
            if redact:
                entry = redact_entry(entry)
            _display_entry(entry, show_date=(len(sessions) > 1))


def _display_entry(entry, show_date: bool = True):
    """Display a single entry."""
    if show_date:
        ts = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    else:
        ts = format_time_short(entry.timestamp)
    
    module = f"[{entry.module}] " if entry.module else ""
    
    if entry.level == 'error':
        icon = click.style("⛔", fg="red")
    else:
        icon = "💡"
    
    # First line of message only, truncated
    msg = entry.message.split('\n')[0]
    if len(msg) > 100:
        msg = msg[:100] + "..."
    
    click.echo()
    click.echo(f"{icon} {click.style(ts, fg='yellow')} {click.style(module, fg='blue')}")
    click.echo(f"   {msg}")
