"""PII redaction utilities for logging."""

import re


# Patterns for PII detection
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b")
# Credit card pattern (basic)
CC_PATTERN = re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b")
# UUID pattern (often used as user IDs)
UUID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE
)


def redact_for_logging(text: str) -> str:
    """
    Redact PII from text before logging.

    Redacts:
    - Email addresses
    - Phone numbers
    - Credit card numbers
    - UUIDs (user IDs)

    Args:
        text: Text that may contain PII

    Returns:
        Text with PII replaced by [REDACTED-<type>]

    Examples:
        >>> redact_for_logging("User john@example.com logged in")
        'User [REDACTED-EMAIL] logged in'

        >>> redact_for_logging("Error for user 123e4567-e89b-12d3-a456-426614174000")
        'Error for user [REDACTED-UUID]'
    """
    if not isinstance(text, str):
        text = str(text)

    # Redact emails
    text = EMAIL_PATTERN.sub("[REDACTED-EMAIL]", text)

    # Redact phone numbers
    text = PHONE_PATTERN.sub("[REDACTED-PHONE]", text)

    # Redact credit cards
    text = CC_PATTERN.sub("[REDACTED-CC]", text)

    # Redact UUIDs (user IDs)
    return UUID_PATTERN.sub("[REDACTED-UUID]", text)
