"""Time utilities for PAI."""
import os
import pytz
from datetime import datetime, timezone
from typing import Optional


def get_timezone() -> pytz.BaseTzInfo:
    """Get configured timezone."""
    tz_name = os.getenv("TIMEZONE", "Europe/London")
    return pytz.timezone(tz_name)


def now() -> datetime:
    """Get current datetime in configured timezone."""
    return datetime.now(get_timezone())


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def to_iso8601(dt: datetime) -> str:
    """Convert datetime to ISO8601 string."""
    if dt.tzinfo is None:
        dt = get_timezone().localize(dt)
    return dt.isoformat()


def from_iso8601(iso_string: str) -> datetime:
    """Parse ISO8601 string to datetime."""
    return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
