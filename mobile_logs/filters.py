"""Filters for log entries."""

from datetime import datetime
from typing import Optional
from .parser import LogEntry


def filter_entries(
    entries: list[LogEntry],
    level: Optional[str] = None,
    module: Optional[str] = None,
    search: Optional[str] = None,
    after: Optional[datetime] = None,
    before: Optional[datetime] = None,
) -> list[LogEntry]:
    """Filter log entries based on criteria.
    
    Args:
        entries: List of LogEntry objects
        level: Filter by level ('info' or 'error')
        module: Filter by module name (case-insensitive partial match)
        search: Filter by text search in message (case-insensitive)
        after: Only entries after this time
        before: Only entries before this time
        
    Returns:
        Filtered list of LogEntry objects
    """
    result = entries
    
    if level:
        result = [e for e in result if e.level == level]
    
    if module:
        module_lower = module.lower()
        result = [e for e in result if e.module and module_lower in e.module.lower()]
    
    if search:
        search_lower = search.lower()
        result = [e for e in result if search_lower in e.message.lower()]
    
    if after:
        result = [e for e in result if e.timestamp >= after]
    
    if before:
        result = [e for e in result if e.timestamp <= before]
    
    return result


def get_errors(entries: list[LogEntry]) -> list[LogEntry]:
    """Get only error entries."""
    return [e for e in entries if e.level == 'error']


def get_context(
    entries: list[LogEntry],
    target: LogEntry,
    before: int = 3,
    after: int = 3
) -> list[LogEntry]:
    """Get entries around a target entry for context.
    
    Args:
        entries: All entries (should be sorted by timestamp)
        target: The entry to get context for
        before: Number of entries before
        after: Number of entries after
        
    Returns:
        List of entries including context
    """
    try:
        idx = entries.index(target)
    except ValueError:
        return [target]
    
    start = max(0, idx - before)
    end = min(len(entries), idx + after + 1)
    return entries[start:end]
