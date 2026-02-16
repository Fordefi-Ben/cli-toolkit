"""Parser for Fordefi mobile log format."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Generator
from pathlib import Path


@dataclass
class LogEntry:
    """A single log entry."""
    timestamp: datetime
    level: str  # 'info' or 'error'
    icon: str
    module: Optional[str]
    message: str
    raw: str
    file_source: str
    line_number: int


@dataclass 
class AppInfo:
    """Application and device info extracted from logs."""
    version: Optional[str] = None
    device_model: Optional[str] = None
    device_type: Optional[str] = None
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    kernel: Optional[str] = None


# Regex patterns
TIMESTAMP_PATTERN = re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\]')
MODULE_PATTERN = re.compile(r'\[([A-Za-z][A-Za-z0-9_]+)\]')
ICON_PATTERN = re.compile(r'│ (.) \[')

# App info patterns
VERSION_PATTERN = re.compile(r'Version: (v[\d.]+)')
DEVICE_MODEL_PATTERN = re.compile(r'Device model: (\w+) ([\w,]+)')
OS_VERSION_PATTERN = re.compile(r'OS version: ([\d.]+)')
SYSTEM_NAME_PATTERN = re.compile(r'System name: (\w+)')
KERNEL_PATTERN = re.compile(r'Darwin Kernel Version ([^\n]+)')


def parse_file(filepath: Path) -> Generator[LogEntry, None, None]:
    """Parse a single log file and yield LogEntry objects.
    
    Args:
        filepath: Path to the log file
        
    Yields:
        LogEntry objects for each log entry
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    current_entry_lines = []
    entry_start_line = 0
    
    for i, line in enumerate(lines):
        # Skip the header line
        if line.startswith('{"version"'):
            continue
        
        # Start of new entry
        if line.startswith('┌'):
            if current_entry_lines:
                entry = _parse_entry(current_entry_lines, filepath.name, entry_start_line)
                if entry:
                    yield entry
            current_entry_lines = [line]
            entry_start_line = i + 1
        else:
            current_entry_lines.append(line)
    
    # Don't forget the last entry
    if current_entry_lines:
        entry = _parse_entry(current_entry_lines, filepath.name, entry_start_line)
        if entry:
            yield entry


def _parse_entry(lines: list[str], filename: str, line_num: int) -> Optional[LogEntry]:
    """Parse a single log entry from its lines."""
    raw = ''.join(lines)
    
    # Extract icon/level
    icon_match = ICON_PATTERN.search(raw)
    if not icon_match:
        return None
    
    icon = icon_match.group(1)
    level = 'error' if icon == '⛔' else 'info'
    
    # Extract timestamp
    ts_match = TIMESTAMP_PATTERN.search(raw)
    if not ts_match:
        return None
    
    try:
        timestamp = datetime.strptime(ts_match.group(1), '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        return None
    
    # Extract module (optional)
    module = None
    module_match = MODULE_PATTERN.search(raw[ts_match.end():])
    if module_match:
        module = module_match.group(1)
    
    # Extract message (everything after timestamp and optional module)
    msg_start = ts_match.end()
    if module_match:
        msg_start += module_match.end()
    
    # Clean up the message - remove box drawing chars and extra whitespace
    message_raw = raw[msg_start:]
    message_lines = []
    for line in message_raw.split('\n'):
        clean = line.strip('│┌└─ \t\n')
        if clean:
            message_lines.append(clean)
    message = '\n'.join(message_lines)
    
    return LogEntry(
        timestamp=timestamp,
        level=level,
        icon=icon,
        module=module,
        message=message,
        raw=raw,
        file_source=filename,
        line_number=line_num
    )


def extract_app_info(filepath: Path) -> AppInfo:
    """Extract app and device info from a log file.
    
    Looks for the INITIALIZE APPLICATION block.
    
    Args:
        filepath: Path to a log file
        
    Returns:
        AppInfo with extracted data
    """
    info = AppInfo()
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read(50000)  # Only need first 50KB
    
    # Look for version
    match = VERSION_PATTERN.search(content)
    if match:
        info.version = match.group(1)
    
    # Device model
    match = DEVICE_MODEL_PATTERN.search(content)
    if match:
        info.device_type = match.group(1)
        info.device_model = match.group(2)
    
    # OS version
    match = OS_VERSION_PATTERN.search(content)
    if match:
        info.os_version = match.group(1)
    
    # System name
    match = SYSTEM_NAME_PATTERN.search(content)
    if match:
        info.os_name = match.group(1)
    
    # Kernel
    match = KERNEL_PATTERN.search(content)
    if match:
        info.kernel = match.group(1).strip()
    
    return info


def get_all_modules(entries: list[LogEntry]) -> set[str]:
    """Get all unique module names from entries."""
    return {e.module for e in entries if e.module}
