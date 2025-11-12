"""Tests for telemetry logging utilities - PII redaction functions."""

from telemetry.logging_utils import redact_for_logging, redact_string


class TestRedactString:
    """Tests for redact_string() function."""

    def test_redacts_none_value(self):
        """Test that None values are handled gracefully."""
        result = redact_string(None)
        assert result == "<None>"

    def test_redacts_empty_string(self):
        """Test that empty strings are handled appropriately."""
        result = redact_string("")
        assert result == "<empty>"

    def test_redacts_single_character_string(self):
        """Test that single character strings are fully masked."""
        result = redact_string("A")
        assert result == "*"
        assert len(result) == 1

    def test_redacts_two_character_string(self):
        """Test that two character strings show first and last with one star."""
        result = redact_string("AB")
        assert result == "A*B"
        assert len(result) == 3

    def test_redacts_short_string_showing_first_and_last(self):
        """Test that short strings show first and last characters with redaction."""
        result = redact_string("secret")
        # "secret" -> "s****t" (1 char visible each end, 4 stars in middle)
        assert result == "s****t"
        assert result[0] == "s"
        assert result[-1] == "t"
        assert len(result) == 6

    def test_redacts_medium_string(self):
        """Test that medium-length strings are properly redacted."""
        result = redact_string("api-key-12345")
        # First and last char visible, rest redacted
        assert result[0] == "a"
        assert result[-1] == "5"
        assert "*" in result
        assert len(result) == 13

    def test_redacts_long_string(self):
        """Test that long strings are properly redacted."""
        result = redact_string("sk-1234567890abcdefghij")
        assert result[0] == "s"
        assert result[-1] == "j"
        assert "*" in result
        assert len(result) == 23

    def test_redacts_with_min_visible_chars_parameter(self):
        """Test that min_visible_chars parameter controls visible characters."""
        # Show 2 chars at each end
        result = redact_string("confidential", min_visible_chars=2)
        assert result[:2] == "co"
        assert result[-2:] == "al"
        assert "*" in result
        assert len(result) == 12

    def test_min_visible_chars_with_short_string(self):
        """Test that min_visible_chars works correctly with short strings."""
        # String length 4, min_visible 2 -> "ab**cd" would be longer, so "a**d"
        result = redact_string("abcd", min_visible_chars=2)
        # With 4 chars and min_visible=2, we can't show 2 on each end (would need 4+)
        # So it should show 1 on each end
        assert result[0] == "a"
        assert result[-1] == "d"

    def test_min_visible_chars_zero(self):
        """Test that min_visible_chars=0 fully redacts the string."""
        result = redact_string("secret", min_visible_chars=0)
        assert result == "******"
        assert "*" in result
        assert "s" not in result
        assert "t" not in result

    def test_redacts_string_with_unicode(self):
        """Test that unicode characters are handled correctly."""
        result = redact_string("café")
        assert result[0] == "c"
        assert result[-1] == "é"
        assert "*" in result

    def test_redacts_string_with_whitespace(self):
        """Test that strings with spaces are handled correctly."""
        result = redact_string("my secret")
        assert result[0] == "m"
        assert result[-1] == "t"
        assert "*" in result
        assert len(result) == 9


class TestRedactForLogging:
    """Tests for redact_for_logging() function."""

    def test_redacts_none_value(self):
        """Test that None values are handled."""
        result = redact_for_logging(None)
        assert result == "<None>"

    def test_redacts_string_value(self):
        """Test that string values are redacted."""
        result = redact_for_logging("password123")
        assert result[0] == "p"
        assert result[-1] == "3"
        assert "*" in result

    def test_redacts_integer_value(self):
        """Test that integer values are converted and redacted."""
        result = redact_for_logging(12345)
        assert result[0] == "1"
        assert result[-1] == "5"
        assert "*" in result

    def test_redacts_float_value(self):
        """Test that float values are converted and redacted."""
        result = redact_for_logging(123.456)
        # "123.456" -> "1*****6"
        assert result[0] == "1"
        assert result[-1] == "6"
        assert "*" in result

    def test_redacts_zero(self):
        """Test that zero value is handled."""
        result = redact_for_logging(0)
        # "0" is single char, should be fully masked
        assert result == "*"

    def test_redacts_negative_number(self):
        """Test that negative numbers are redacted correctly."""
        result = redact_for_logging(-12345)
        # "-12345" -> "-****5"
        assert result[0] == "-"
        assert result[-1] == "5"
        assert "*" in result

    def test_redacts_empty_string(self):
        """Test that empty strings are handled."""
        result = redact_for_logging("")
        assert result == "<empty>"

    def test_redacts_boolean_value(self):
        """Test that boolean values are converted and redacted."""
        result_true = redact_for_logging(True)
        result_false = redact_for_logging(False)
        # "True" -> "T**e", "False" -> "F***e"
        assert result_true[0] == "T"
        assert result_true[-1] == "e"
        assert result_false[0] == "F"
        assert result_false[-1] == "e"
