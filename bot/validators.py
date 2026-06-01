"""Input validation helpers."""

from decimal import Decimal, InvalidOperation
import re


class ValidationError(ValueError):
    """Raised when an order input is invalid."""


def validate_symbol(value: str) -> str:
    symbol = value.strip().upper()
    if not symbol:
        raise ValidationError("Symbol is required.")
    if not re.fullmatch(r"[A-Z0-9]+", symbol):
        raise ValidationError("Symbol may only contain letters and numbers.")
    return symbol


def validate_side(value: str) -> str:
    return _validate_choice("Side", value, {"BUY", "SELL"})


def validate_order_type(value: str) -> str:
    return _validate_choice("Order type", value, {"MARKET", "LIMIT"})


def validate_positive_decimal(name: str, value: str | Decimal) -> Decimal:
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValidationError(f"{name} must be numeric.") from None

    if not number.is_finite() or number <= 0:
        raise ValidationError(f"{name} must be greater than zero.")
    return number


def _validate_choice(name: str, value: str, accepted: set[str]) -> str:
    normalized = value.strip().upper()
    if normalized not in accepted:
        choices = "/".join(sorted(accepted))
        raise ValidationError(f"{name} must be one of: {choices}.")
    return normalized

