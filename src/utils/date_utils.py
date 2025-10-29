"""Utility functions for date parsing, validation, and formatting.

Provides consistent date handling across the application for ISO 8601
date strings and datetime objects.
"""


def validate_date(date_string):
    """Validate if a string represents a valid date in YYYY-MM-DD format.

    Args:
        date_string: String to validate

    Returns:
        True if valid YYYY-MM-DD date, False otherwise
    """
    from datetime import datetime

    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def format_date(date):
    """Format a date object as YYYY-MM-DD string.

    Args:
        date: datetime.date object or None

    Returns:
        Date string in YYYY-MM-DD format, or None if input is None
    """
    return date.strftime("%Y-%m-%d") if date else None


def get_today_date():
    """Get today's date.

    Returns:
        datetime.date object representing today
    """
    from datetime import datetime

    return datetime.today().date()
