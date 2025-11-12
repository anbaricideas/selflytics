"""Unit tests for password hashing utilities."""

import pytest

from app.auth.password import hash_password, verify_password


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_produces_verifiable_hash(self):
        """Test that hash_password produces a hash that can be verified."""
        password = "secure_password_123"  # noqa: S105
        hashed = hash_password(password)

        # Hash should differ from plaintext and be verifiable
        assert hashed != password
        assert len(hashed) > 0
        assert verify_password(password, hashed)

    def test_hash_password_uses_salt_for_randomness(self):
        """Test that identical passwords produce different hashes (salted)."""
        password = "same_password"  # noqa: S105
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Different hashes prove salt is being used
        assert hash1 != hash2
        # But both should verify the original password
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_verify_password_with_correct_password(self):
        """Test that verify_password returns True for correct password."""
        password = "correct_password"  # noqa: S105
        hashed = hash_password(password)

        assert verify_password(password, hashed)

    def test_verify_password_with_incorrect_password(self):
        """Test that verify_password returns False for incorrect password."""
        correct_password = "correct_password"  # noqa: S105
        wrong_password = "wrong_password"  # noqa: S105
        hashed = hash_password(correct_password)

        assert not verify_password(wrong_password, hashed)

    def test_verify_password_with_empty_password(self):
        """Test that verify_password handles empty passwords."""
        password = "test_password"  # noqa: S105
        hashed = hash_password(password)

        assert not verify_password("", hashed)

    def test_hash_password_accepts_empty_string(self):
        """Test that hash_password accepts empty strings."""
        hashed = hash_password("")
        assert len(hashed) > 0
        assert verify_password("", hashed)

    def test_verify_password_with_special_characters(self):
        """Test that passwords with special characters work correctly."""
        password = "p@ssw0rd!#$%^&*()"  # noqa: S105
        hashed = hash_password(password)

        assert verify_password(password, hashed)

    def test_verify_password_with_unicode(self):
        """Test that passwords with unicode characters work correctly."""
        password = "пароль密码🔒"  # noqa: S105
        hashed = hash_password(password)

        assert verify_password(password, hashed)

    def test_verify_password_with_long_password(self):
        """Test that very long passwords are handled correctly.

        Note: Bcrypt truncates passwords at 72 bytes. This test verifies
        that long passwords still hash and verify correctly.
        """
        password = "a" * 100
        hashed = hash_password(password)

        assert verify_password(password, hashed)

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "CaseSensitive123"  # noqa: S105
        hashed = hash_password(password)

        assert not verify_password("casesensitive123", hashed)
        assert not verify_password("CASESENSITIVE123", hashed)
        assert verify_password(password, hashed)

    def test_verify_password_with_invalid_hash_format(self):
        """Test that verify_password safely handles malformed hashes."""
        password = "test_password"  # noqa: S105

        # Should return False (not raise exception) for invalid hashes
        assert not verify_password(password, "not_a_hash")
        assert not verify_password(password, "")
        assert not verify_password(password, "$2b$12$")  # truncated

    def test_hash_password_with_none_raises_error(self):
        """Test that hash_password rejects None input."""
        with pytest.raises((TypeError, AttributeError)):
            hash_password(None)

    def test_verify_password_with_none_inputs_returns_false(self):
        """Test that verify_password safely handles None inputs.

        Note: verify_password returns False for invalid inputs rather than
        raising exceptions, making it safe to use in authentication flows.
        """
        hashed = hash_password("password")

        # None inputs should return False, not raise exceptions
        assert not verify_password(None, hashed)
        assert not verify_password("password", None)
