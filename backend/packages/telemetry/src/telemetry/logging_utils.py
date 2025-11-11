"""Logging utilities for secure telemetry - PII redaction functions."""


def redact_string(value: str | None, min_visible_chars: int = 1) -> str:
    """Redact a string for safe logging, showing only first and last characters.

    Args:
        value: The string to redact (or None)
        min_visible_chars: Minimum number of characters to show at start and end (default: 1)

    Returns:
        Redacted string with first/last characters visible and middle replaced with asterisks.
        Special cases:
        - None -> "<None>"
        - Empty string -> "<empty>"
        - Single char -> "*"
        - min_visible_chars=0 -> all asterisks

    Examples:
        >>> redact_string("secret")
        's****t'
        >>> redact_string("api-key-12345")
        'a***********5'
        >>> redact_string("AB")
        'A*B'
        >>> redact_string(None)
        '<None>'
        >>> redact_string("", min_visible_chars=0)
        '******'
    """
    if value is None:
        return "<None>"
    if not value:
        return "<empty>"

    # Handle min_visible_chars=0 (full redaction)
    if min_visible_chars == 0:
        return "*" * len(value)

    # Single character string - fully masked
    if len(value) <= min_visible_chars:
        return "*" * len(value)

    # Two character string or very short strings
    # Always show first char, one star, and last char
    if len(value) <= min_visible_chars * 2:
        return f"{value[0]}*{value[-1]}"

    # Normal case: show min_visible_chars at start and end
    visible_start = value[:min_visible_chars]
    visible_end = value[-min_visible_chars:]
    redacted_length = len(value) - (min_visible_chars * 2)
    return f"{visible_start}{'*' * redacted_length}{visible_end}"


def redact_for_logging(value: str | int | float | bool | None) -> str:
    """Redact any value for safe logging.

    Args:
        value: The value to redact (str, int, float, bool, or None)

    Returns:
        Redacted string representation of the value.

    Examples:
        >>> redact_for_logging("password123")
        'p*********3'
        >>> redact_for_logging(12345)
        '1***5'
        >>> redact_for_logging(None)
        '<None>'
        >>> redact_for_logging(True)
        'T**e'
    """
    if value is None:
        return "<None>"
    if isinstance(value, bool):
        # Handle bool before int check (bool is subclass of int in Python)
        return redact_string(str(value))
    if isinstance(value, int | float):
        return redact_string(str(value))
    if isinstance(value, str):
        return redact_string(value)
    return redact_string(str(value))
