"""Shared input validation rules"""
from datetime import datetime, date


def validate_positive_amount(value):
    """Returns (is_valid, error_message_or_None)."""
    if value is None:
        return False, "Amount is required"
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return False, "Amount must be a number"
    if amount <= 0:
        return False, "Amount must be greater than zero"
    return True, None


def validate_non_negative_amount(value):
    """For budgets, which may legitimately be 0 (not yet set)."""
    if value is None:
        return True, None  # optional field
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return False, "Budget must be a number"
    if amount < 0:
        return False, "Budget cannot be negative"
    return True, None


def validate_not_future_date(date_str):
    """Expects ISO format YYYY-MM-DD. Returns (is_valid, error_message_or_None)."""
    if not date_str:
        return False, "Date is required"
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return False, "Date must be in YYYY-MM-DD format"
    if parsed > date.today():
        return False, "Date cannot be in the future"
    return True, None

def validate_future_date(date_str):
    """For savings goal target dates, which must be upcoming, not past."""
    if not date_str:
        return False, "Date is required"
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return False, "Date must be in YYYY-MM-DD format"
    if parsed <= date.today():
        return False, "Target date must be in the future"
    return True, None