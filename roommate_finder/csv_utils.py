"""Helpers for CSV downloads."""


def safe_cell(value):
    """Stops spreadsheet programs from running user-typed text as a formula (CSV injection)."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text
