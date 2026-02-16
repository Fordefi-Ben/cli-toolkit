"""Redact sensitive information from logs."""

import re
from .parser import LogEntry


# Patterns for sensitive data
PATTERNS = {
    'email': (re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'), '[EMAIL]'),
    'uuid': (re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.I), '[UUID]'),
    'firebase_token': (re.compile(r'[a-zA-Z0-9_-]{100,}:APA91[a-zA-Z0-9_-]+'), '[FCM_TOKEN]'),
    'base64_key': (re.compile(r'eyJ[a-zA-Z0-9+/=]{50,}'), '[ENCRYPTED_KEY]'),
    'ios_path': (re.compile(r'/var/mobile/Containers/[^\s]+'), '[IOS_PATH]'),
}


def redact_text(text: str) -> str:
    """Redact sensitive information from text.
    
    Args:
        text: Input text
        
    Returns:
        Text with sensitive data replaced
    """
    result = text
    for name, (pattern, replacement) in PATTERNS.items():
        result = pattern.sub(replacement, result)
    return result


def redact_entry(entry: LogEntry) -> LogEntry:
    """Create a redacted copy of a log entry.
    
    Args:
        entry: Original log entry
        
    Returns:
        New LogEntry with redacted message and raw text
    """
    return LogEntry(
        timestamp=entry.timestamp,
        level=entry.level,
        icon=entry.icon,
        module=entry.module,
        message=redact_text(entry.message),
        raw=redact_text(entry.raw),
        file_source=entry.file_source,
        line_number=entry.line_number
    )


def redact_entries(entries: list[LogEntry]) -> list[LogEntry]:
    """Redact a list of entries.
    
    Args:
        entries: List of log entries
        
    Returns:
        List of redacted entries
    """
    return [redact_entry(e) for e in entries]
