"""Session grouping utilities for mobile logs."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Generator
import click

from .parser import LogEntry
from .datetime_utils import format_datetime_human, format_duration, format_time_short


# Default gap threshold in seconds (5 minutes)
DEFAULT_GAP_THRESHOLD = 300


@dataclass
class Session:
    """A group of log entries that form a session."""
    entries: List[LogEntry] = field(default_factory=list)
    index: int = 0  # 1-based session number
    
    @property
    def start_time(self) -> Optional[datetime]:
        return self.entries[0].timestamp if self.entries else None
    
    @property
    def end_time(self) -> Optional[datetime]:
        return self.entries[-1].timestamp if self.entries else None
    
    @property
    def duration_seconds(self) -> float:
        if len(self.entries) < 2:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def entry_count(self) -> int:
        return len(self.entries)
    
    @property
    def error_count(self) -> int:
        return sum(1 for e in self.entries if e.level == 'error')
    
    def __len__(self) -> int:
        return len(self.entries)
    
    def __iter__(self):
        return iter(self.entries)


def group_by_sessions(
    entries: List[LogEntry],
    gap_threshold_seconds: float = DEFAULT_GAP_THRESHOLD
) -> List[Session]:
    """
    Group log entries into sessions based on time gaps.
    
    A new session starts when the gap between consecutive entries
    exceeds the threshold.
    
    Args:
        entries: List of LogEntry objects (should be sorted by timestamp)
        gap_threshold_seconds: Gap threshold in seconds (default: 300 = 5 minutes)
        
    Returns:
        List of Session objects
    """
    if not entries:
        return []
    
    # Ensure entries are sorted
    sorted_entries = sorted(entries, key=lambda e: e.timestamp)
    
    sessions = []
    current_session = Session(index=1)
    current_session.entries.append(sorted_entries[0])
    
    for entry in sorted_entries[1:]:
        prev_entry = current_session.entries[-1]
        gap = (entry.timestamp - prev_entry.timestamp).total_seconds()
        
        if gap > gap_threshold_seconds:
            # Start a new session
            sessions.append(current_session)
            current_session = Session(index=len(sessions) + 1)
        
        current_session.entries.append(entry)
    
    # Don't forget the last session
    if current_session.entries:
        sessions.append(current_session)
    
    return sessions


def format_session_header(
    session: Session,
    width: int = 70,
    show_errors: bool = True
) -> str:
    """
    Generate a visual session separator header.
    
    Args:
        session: The Session object
        width: Total width of the header line
        show_errors: Whether to include error count
        
    Returns:
        Formatted header string like:
        "━━━ Session 1 • Jan 15, 11:06 AM (47 entries, 3.2s) ━━━"
    """
    if not session.entries:
        return "━" * width
    
    # Build the info string
    time_str = format_datetime_human(session.start_time)
    duration_str = format_duration(session.duration_seconds)
    
    parts = [f"{session.entry_count} entries"]
    if session.duration_seconds > 0:
        parts.append(duration_str)
    if show_errors and session.error_count > 0:
        parts.append(f"{session.error_count} errors")
    
    info_str = ", ".join(parts)
    
    content = f" Session {session.index} • {time_str} ({info_str}) "
    
    # Calculate padding
    remaining = width - len(content)
    left_pad = remaining // 2
    right_pad = remaining - left_pad
    
    return "━" * left_pad + content + "━" * right_pad


def format_session_header_compact(session: Session) -> str:
    """
    Generate a compact session header for dense output.
    
    Returns:
        Compact header like "── Jan 15, 11:06 AM ──"
    """
    if not session.entries:
        return "─" * 40
    
    time_str = format_datetime_human(session.start_time)
    return f"── {time_str} ──"


def display_entries_grouped(
    entries: List[LogEntry],
    display_func,
    gap_threshold_seconds: float = DEFAULT_GAP_THRESHOLD,
    show_session_headers: bool = True,
    header_width: int = 70
) -> None:
    """
    Display entries grouped by session.
    
    Args:
        entries: List of LogEntry objects
        display_func: Function to call for each entry (entry) -> None
        gap_threshold_seconds: Gap threshold for session detection
        show_session_headers: Whether to show session headers
        header_width: Width of session header lines
    """
    if not entries:
        return
    
    sessions = group_by_sessions(entries, gap_threshold_seconds)
    
    for session in sessions:
        if show_session_headers and len(sessions) > 1:
            click.echo()
            click.echo(click.style(
                format_session_header(session, header_width),
                fg="cyan"
            ))
        
        for entry in session.entries:
            display_func(entry)


def iter_entries_with_session_breaks(
    entries: List[LogEntry],
    gap_threshold_seconds: float = DEFAULT_GAP_THRESHOLD
) -> Generator[tuple, None, None]:
    """
    Iterate over entries, yielding session info.
    
    Yields:
        Tuples of (entry, session, is_first_in_session)
    """
    sessions = group_by_sessions(entries, gap_threshold_seconds)
    
    for session in sessions:
        for i, entry in enumerate(session.entries):
            yield (entry, session, i == 0)


def get_session_stats(sessions: List[Session]) -> dict:
    """
    Calculate aggregate statistics across sessions.
    
    Args:
        sessions: List of Session objects
        
    Returns:
        Dictionary with stats like total_entries, total_errors, avg_session_duration
    """
    if not sessions:
        return {
            'session_count': 0,
            'total_entries': 0,
            'total_errors': 0,
            'total_duration_seconds': 0,
            'avg_session_duration_seconds': 0,
            'avg_entries_per_session': 0,
        }
    
    total_entries = sum(s.entry_count for s in sessions)
    total_errors = sum(s.error_count for s in sessions)
    total_duration = sum(s.duration_seconds for s in sessions)
    
    return {
        'session_count': len(sessions),
        'total_entries': total_entries,
        'total_errors': total_errors,
        'total_duration_seconds': total_duration,
        'avg_session_duration_seconds': total_duration / len(sessions),
        'avg_entries_per_session': total_entries / len(sessions),
    }
