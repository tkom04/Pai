"""Time utilities for PAI."""
import os
import pytz
from datetime import datetime, timezone, date, time as dt_time
from typing import Optional, Union
from zoneinfo import ZoneInfo


def get_timezone() -> pytz.BaseTzInfo:
    """Get configured timezone."""
    tz_name = os.getenv("TIMEZONE", "Europe/London")
    return pytz.timezone(tz_name)


def now() -> datetime:
    """Get current datetime in configured timezone."""
    return datetime.now(timezone.utc)


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def to_iso8601(dt: datetime) -> str:
    """Convert datetime to ISO8601 string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def from_iso8601(iso_string: str) -> datetime:
    """Parse ISO8601 string to datetime."""
    return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))


def to_aware_utc(dt_or_str: Union[str, datetime, None], default_tz: str = "Europe/London") -> Optional[datetime]:
    """
    Convert any datetime or ISO8601 string to timezone-aware UTC datetime.

    This is the comprehensive fix for "can't compare offset-naive and offset-aware datetimes".

    Args:
        dt_or_str: ISO8601 string, datetime object, or None
        default_tz: Timezone to assume for naive datetimes (defaults to Europe/London for BST/GMT handling)

    Returns:
        Timezone-aware UTC datetime, or None if input is None

    Examples:
        >>> to_aware_utc("2025-10-11T11:11:00+00:00")  # Already aware → UTC
        >>> to_aware_utc("2025-10-11T11:11:00")         # Naive → treated as Europe/London → UTC
        >>> to_aware_utc(datetime.now())                 # Naive → treated as Europe/London → UTC
        >>> to_aware_utc(datetime.now(timezone.utc))    # Already aware → UTC (no change)
    """
    if dt_or_str is None:
        return None

    # Handle string input
    if isinstance(dt_or_str, str):
        # Normalize 'Z' to '+00:00' for consistent parsing
        s = dt_or_str.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
        except ValueError as e:
            raise ValueError(f"Invalid ISO8601 datetime string: {dt_or_str}") from e
    elif isinstance(dt_or_str, datetime):
        dt = dt_or_str
    else:
        raise TypeError(f"Unsupported type for to_aware_utc: {type(dt_or_str)}")

    # If naive (no timezone info), assume the default timezone
    if dt.tzinfo is None:
        try:
            dt = dt.replace(tzinfo=ZoneInfo(default_tz))
        except Exception:
            # Fallback to UTC if ZoneInfo fails
            dt = dt.replace(tzinfo=timezone.utc)

    # Convert to UTC
    return dt.astimezone(timezone.utc)


def make_aware(dt):
    """
    Convert naive datetime to timezone-aware UTC datetime.

    DEPRECATED: Use to_aware_utc() instead for more comprehensive handling.
    """
    if dt is None:
        return None

    # If it's a date object (not datetime), convert to datetime at midnight
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime.combine(dt, dt_time.min)

    # Now handle timezone awareness
    if isinstance(dt, datetime) and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt
