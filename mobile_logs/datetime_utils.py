"""Flexible datetime parsing utilities for mobile logs."""

import re
from datetime import datetime, date, time, timedelta
from typing import Optional, Tuple
from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta


class DateTimeParseResult:
    """Result of parsing a datetime string."""
    
    def __init__(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        time_only: Optional[time] = None,
        original: str = ""
    ):
        self.start = start
        self.end = end
        self.time_only = time_only  # For time-only queries (filter any date with this time)
        self.original = original
    
    @property
    def is_range(self) -> bool:
        return self.start != self.end
    
    @property
    def is_time_only(self) -> bool:
        return self.time_only is not None


# Patterns for detecting input type
TIME_ONLY_PATTERN = re.compile(
    r'^(\d{1,2})(?::(\d{2}))?(?::(\d{2}))?\s*(am|pm)?$',
    re.IGNORECASE
)
MONTH_DAY_PATTERN = re.compile(
    r'^(\d{1,2})[-/](\d{1,2})$'
)
NAMED_MONTH_PATTERN = re.compile(
    r'^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})(?:\s+(.+))?$',
    re.IGNORECASE
)
MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
}


def parse_flexible_datetime(
    input_str: str,
    reference_date: Optional[date] = None
) -> DateTimeParseResult:
    """
    Parse a flexible datetime string into a DateTimeParseResult.
    
    Supported formats:
    - ISO date: 2026-01-15
    - ISO datetime: 2026-01-15T10:30 or 2026-01-15 10:30
    - Month-day: 01-15, 1/15
    - Named month: jan 15, january 15
    - Time only: 10:00, 10:30:00, 10pm, 10:30pm
    - Combined: jan 15 10pm, 01-15 22:00
    
    Args:
        input_str: The datetime string to parse
        reference_date: Reference date for relative parsing (defaults to today)
        
    Returns:
        DateTimeParseResult with start/end range or time_only
        
    Raises:
        ValueError: If the string cannot be parsed
    """
    if reference_date is None:
        reference_date = date.today()
    
    input_str = input_str.strip()
    original = input_str
    
    if not input_str:
        raise ValueError("Empty datetime string")
    
    # Try time-only pattern first
    time_match = TIME_ONLY_PATTERN.match(input_str)
    if time_match:
        return _parse_time_only(time_match, original)
    
    # Try month-day pattern (01-15 or 1/15)
    md_match = MONTH_DAY_PATTERN.match(input_str)
    if md_match:
        return _parse_month_day(md_match, reference_date, original)
    
    # Try named month pattern (jan 15, january 15 10pm)
    named_match = NAMED_MONTH_PATTERN.match(input_str)
    if named_match:
        return _parse_named_month(named_match, reference_date, original)
    
    # Fall back to dateutil parser for ISO and other standard formats
    return _parse_with_dateutil(input_str, reference_date, original)


def _parse_time_only(match: re.Match, original: str) -> DateTimeParseResult:
    """Parse a time-only string like '10:30' or '10pm'."""
    hour = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    second = int(match.group(3)) if match.group(3) else 0
    ampm = match.group(4)
    
    if ampm:
        ampm = ampm.lower()
        if ampm == 'pm' and hour != 12:
            hour += 12
        elif ampm == 'am' and hour == 12:
            hour = 0
    
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        raise ValueError(f"Invalid time: {original}")
    
    return DateTimeParseResult(
        time_only=time(hour, minute, second),
        original=original
    )


def _parse_month_day(
    match: re.Match,
    reference_date: date,
    original: str
) -> DateTimeParseResult:
    """Parse month-day like '01-15' or '1/15'."""
    month = int(match.group(1))
    day = int(match.group(2))
    
    if not (1 <= month <= 12 and 1 <= day <= 31):
        raise ValueError(f"Invalid month-day: {original}")
    
    try:
        parsed_date = date(reference_date.year, month, day)
    except ValueError as e:
        raise ValueError(f"Invalid date: {original}") from e
    
    return _date_to_range(parsed_date, original)


def _parse_named_month(
    match: re.Match,
    reference_date: date,
    original: str
) -> DateTimeParseResult:
    """Parse named month like 'jan 15' or 'january 15 10pm'."""
    month_str = match.group(1).lower()[:3]
    month = MONTH_MAP.get(month_str)
    day = int(match.group(2))
    time_part = match.group(3)
    
    if month is None:
        raise ValueError(f"Invalid month: {original}")
    
    if not (1 <= day <= 31):
        raise ValueError(f"Invalid day: {original}")
    
    try:
        parsed_date = date(reference_date.year, month, day)
    except ValueError as e:
        raise ValueError(f"Invalid date: {original}") from e
    
    if time_part:
        # Parse the time part
        time_result = parse_flexible_datetime(time_part.strip(), reference_date)
        if time_result.is_time_only:
            # Combine date with time
            dt = datetime.combine(parsed_date, time_result.time_only)
            return DateTimeParseResult(start=dt, end=dt, original=original)
        else:
            raise ValueError(f"Invalid time in: {original}")
    
    return _date_to_range(parsed_date, original)


def _parse_with_dateutil(
    input_str: str,
    reference_date: date,
    original: str
) -> DateTimeParseResult:
    """Parse using dateutil for standard formats."""
    try:
        # Try parsing with dateutil
        parsed = dateutil_parser.parse(input_str, default=datetime.combine(reference_date, time(0, 0)))
        
        # Check if time was specified by looking for time indicators in input
        has_time = any(c in input_str for c in [':', 'T']) or \
                   any(x in input_str.lower() for x in ['am', 'pm'])
        
        if has_time:
            # Exact datetime specified
            return DateTimeParseResult(start=parsed, end=parsed, original=original)
        else:
            # Date only - return range for entire day
            return _date_to_range(parsed.date(), original)
            
    except (ValueError, TypeError) as e:
        raise ValueError(f"Could not parse datetime: {original}") from e


def _date_to_range(d: date, original: str) -> DateTimeParseResult:
    """Convert a date to a start/end range covering the entire day."""
    start = datetime.combine(d, time(0, 0, 0))
    end = datetime.combine(d, time(23, 59, 59, 999999))
    return DateTimeParseResult(start=start, end=end, original=original)


def parse_datetime_filter(
    input_str: str,
    filter_type: str = 'after',
    reference_date: Optional[date] = None
) -> datetime:
    """
    Parse a datetime string for use as a filter boundary.
    
    For 'after' filters with date-only input, returns start of day.
    For 'before' filters with date-only input, returns end of day.
    
    Args:
        input_str: The datetime string to parse
        filter_type: 'after' or 'before'
        reference_date: Reference date for relative parsing
        
    Returns:
        datetime suitable for filtering
        
    Raises:
        ValueError: If the string cannot be parsed
    """
    result = parse_flexible_datetime(input_str, reference_date)
    
    if result.is_time_only:
        raise ValueError(
            f"Time-only values ('{input_str}') cannot be used as {filter_type} filters. "
            "Please include a date."
        )
    
    if filter_type == 'after':
        return result.start
    else:  # before
        return result.end


def format_datetime_human(dt: datetime, include_date: bool = True) -> str:
    """
    Format a datetime in a human-readable way.
    
    Args:
        dt: The datetime to format
        include_date: Whether to include the date portion
        
    Returns:
        Human-readable string like "Jan 15, 11:06 AM" or "11:06 AM"
    """
    if include_date:
        return dt.strftime('%b %d, %I:%M %p').replace(' 0', ' ').replace('AM', 'AM').replace('PM', 'PM')
    else:
        return dt.strftime('%I:%M %p').lstrip('0').replace(' 0', ' ')


def format_time_short(dt: datetime) -> str:
    """Format time in short form like '11:06:33.048'."""
    return dt.strftime('%H:%M:%S.') + f'{dt.microsecond // 1000:03d}'


def format_duration(seconds: float) -> str:
    """Format a duration in human-readable form."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
