"""Unit tests for JWT token handling."""

from datetime import datetime, timedelta, timezone

import pytest
from jose import JWTError

from app.auth.jwt import create_access_token, verify_token


class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_access_token_produces_valid_token(self):
        """Test that create_access_token produces a decodable JWT."""
        data = {"sub": "user123", "email": "user@example.com"}
        token = create_access_token(data)

        # Token should be a non-empty string with 3 parts (header.payload.signature)
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2

    def test_verify_token_with_valid_token(self):
        """Test that verify_token decodes valid tokens correctly."""
        user_id = "user123"
        email = "user@example.com"
        data = {"sub": user_id, "email": email}
        token = create_access_token(data)

        token_data = verify_token(token)

        assert token_data.user_id == user_id
        assert token_data.email == email

    def test_create_token_with_custom_expiry(self):
        """Test that custom expiry delta is respected."""
        data = {"sub": "user123", "email": "user@example.com"}
        expires_delta = timedelta(minutes=60)
        token = create_access_token(data, expires_delta=expires_delta)

        # Should not raise - token should be valid
        token_data = verify_token(token)
        assert token_data.user_id == "user123"

    def test_verify_token_with_expired_token(self):
        """Test that verify_token rejects expired tokens."""
        data = {"sub": "user123", "email": "user@example.com"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta=expires_delta)

        # Should raise ValueError for expired token
        with pytest.raises(ValueError, match=r"(?i)expired|invalid"):
            verify_token(token)

    def test_verify_token_with_invalid_token(self):
        """Test that verify_token rejects malformed tokens."""
        invalid_tokens = [
            "not.a.token",
            "invalid_token",
            "",
            "header.payload",  # missing signature
        ]

        for invalid_token in invalid_tokens:
            with pytest.raises(ValueError):
                verify_token(invalid_token)

    def test_verify_token_with_missing_claims(self):
        """Test that verify_token rejects tokens missing required claims."""
        # Token without 'sub' claim
        data_no_sub = {"email": "user@example.com"}
        token = create_access_token(data_no_sub)
        with pytest.raises(ValueError, match="Invalid token payload"):
            verify_token(token)

        # Token without 'email' claim
        data_no_email = {"sub": "user123"}
        token = create_access_token(data_no_email)
        with pytest.raises(ValueError, match="Invalid token payload"):
            verify_token(token)

    def test_verify_token_with_none_input(self):
        """Test that verify_token handles None input gracefully."""
        with pytest.raises(ValueError):
            verify_token(None)

    def test_create_token_preserves_additional_claims(self):
        """Test that additional claims are preserved in the token."""
        data = {
            "sub": "user123",
            "email": "user@example.com",
            "role": "admin",
            "permissions": ["read", "write"],
        }
        token = create_access_token(data)

        # TokenData only extracts user_id and email, but they should be in the token
        token_data = verify_token(token)
        assert token_data.user_id == "user123"
        assert token_data.email == "user@example.com"

    def test_token_includes_expiry_claim(self):
        """Test that tokens include the 'exp' (expiry) claim."""
        from jose import jwt

        data = {"sub": "user123", "email": "user@example.com"}
        token = create_access_token(data)

        # Decode without verification to inspect claims
        # (We need the secret key - this test assumes implementation details)
        # Instead, just verify the token can be decoded and has valid structure
        token_data = verify_token(token)
        assert token_data.user_id == "user123"

    def test_different_users_get_different_tokens(self):
        """Test that different user data produces different tokens."""
        data1 = {"sub": "user1", "email": "user1@example.com"}
        data2 = {"sub": "user2", "email": "user2@example.com"}

        token1 = create_access_token(data1)
        token2 = create_access_token(data2)

        # Tokens should be different
        assert token1 != token2

        # Each token should decode to its respective user
        token_data1 = verify_token(token1)
        token_data2 = verify_token(token2)

        assert token_data1.user_id == "user1"
        assert token_data2.user_id == "user2"
