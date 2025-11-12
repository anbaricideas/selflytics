"""Unit tests for token encryption utilities."""

import base64
import binascii
import json
from unittest.mock import MagicMock, patch

import pytest

from app.utils.encryption import decrypt_token, encrypt_token


class TestTokenEncryption:
    """Tests for token encryption and decryption."""

    @patch("app.utils.encryption.kms.KeyManagementServiceClient")
    def test_encrypt_token_returns_base64_string(self, mock_kms_client):
        """Test encrypt_token returns base64-encoded string."""
        # Mock KMS response
        mock_client_instance = MagicMock()
        mock_kms_client.return_value = mock_client_instance

        mock_encrypt_response = MagicMock()
        mock_encrypt_response.ciphertext = b"encrypted_data_here"
        mock_client_instance.encrypt.return_value = mock_encrypt_response

        token_dict = {"oauth_token": "token123", "oauth_token_secret": "secret123"}

        encrypted = encrypt_token(token_dict)

        # Should return base64-encoded string
        assert isinstance(encrypted, str)
        # Should be valid base64
        base64.b64decode(encrypted)
        # Should have called KMS encrypt
        mock_client_instance.encrypt.assert_called_once()

    @patch("app.utils.encryption.kms.KeyManagementServiceClient")
    def test_encrypt_token_serializes_dict(self, mock_kms_client):
        """Test encrypt_token properly serializes token dict."""
        mock_client_instance = MagicMock()
        mock_kms_client.return_value = mock_client_instance

        mock_encrypt_response = MagicMock()
        mock_encrypt_response.ciphertext = b"encrypted_data"
        mock_client_instance.encrypt.return_value = mock_encrypt_response

        token_dict = {"key1": "value1", "key2": "value2"}

        encrypt_token(token_dict)

        # Verify the plaintext passed to KMS is JSON-serialized dict
        call_args = mock_client_instance.encrypt.call_args
        request = call_args.kwargs["request"]
        plaintext = request["plaintext"]

        # Should be JSON-encoded dict
        decoded = json.loads(plaintext.decode("utf-8"))
        assert decoded == token_dict

    @patch("app.utils.encryption.kms.KeyManagementServiceClient")
    def test_encrypt_token_different_outputs(self, mock_kms_client):
        """Test encrypt_token produces different ciphertext each time (KMS behavior)."""
        mock_client_instance = MagicMock()
        mock_kms_client.return_value = mock_client_instance

        # Simulate KMS producing different ciphertext each call
        call_count = [0]

        def mock_encrypt(request):
            call_count[0] += 1
            response = MagicMock()
            response.ciphertext = f"encrypted_data_{call_count[0]}".encode()
            return response

        mock_client_instance.encrypt = mock_encrypt

        token_dict = {"oauth_token": "token123"}

        encrypted1 = encrypt_token(token_dict)
        encrypted2 = encrypt_token(token_dict)

        # Different ciphertext for same input (KMS adds randomness)
        assert encrypted1 != encrypted2

    @patch("app.utils.encryption.kms.KeyManagementServiceClient")
    def test_decrypt_token_returns_dict(self, mock_kms_client):
        """Test decrypt_token returns original dict."""
        mock_client_instance = MagicMock()
        mock_kms_client.return_value = mock_client_instance

        original_token = {"oauth_token": "token123", "oauth_token_secret": "secret123"}
        plaintext_bytes = json.dumps(original_token).encode("utf-8")

        mock_decrypt_response = MagicMock()
        mock_decrypt_response.plaintext = plaintext_bytes
        mock_client_instance.decrypt.return_value = mock_decrypt_response

        encrypted_token = base64.b64encode(b"some_encrypted_data").decode("utf-8")

        decrypted = decrypt_token(encrypted_token)

        assert decrypted == original_token
        mock_client_instance.decrypt.assert_called_once()

    @patch("app.utils.encryption.kms.KeyManagementServiceClient")
    def test_decrypt_token_decodes_base64(self, mock_kms_client):
        """Test decrypt_token properly decodes base64 ciphertext."""
        mock_client_instance = MagicMock()
        mock_kms_client.return_value = mock_client_instance

        mock_decrypt_response = MagicMock()
        mock_decrypt_response.plaintext = b'{"key": "value"}'
        mock_client_instance.decrypt.return_value = mock_decrypt_response

        ciphertext = b"encrypted_ciphertext"
        encrypted_token = base64.b64encode(ciphertext).decode("utf-8")

        decrypt_token(encrypted_token)

        # Verify KMS decrypt was called with decoded ciphertext
        call_args = mock_client_instance.decrypt.call_args
        request = call_args.kwargs["request"]
        assert request["ciphertext"] == ciphertext

    @patch("app.utils.encryption.kms.KeyManagementServiceClient")
    def test_round_trip_encryption(self, mock_kms_client):
        """Test encrypt -> decrypt round trip recovers original data."""
        mock_client_instance = MagicMock()
        mock_kms_client.return_value = mock_client_instance

        original_token = {
            "oauth_token": "test_token",
            "oauth_token_secret": "test_secret",
            "extra_field": "extra_value",
        }

        # Mock encrypt: store plaintext, return fake ciphertext
        stored_plaintext = None

        def mock_encrypt(request):
            nonlocal stored_plaintext
            stored_plaintext = request["plaintext"]
            response = MagicMock()
            response.ciphertext = b"fake_encrypted_data"
            return response

        def mock_decrypt(request):
            # Return the stored plaintext
            response = MagicMock()
            response.plaintext = stored_plaintext
            return response

        mock_client_instance.encrypt = mock_encrypt
        mock_client_instance.decrypt = mock_decrypt

        # Encrypt
        encrypted = encrypt_token(original_token)

        # Decrypt
        decrypted = decrypt_token(encrypted)

        # Should recover original
        assert decrypted == original_token

    @patch("app.utils.encryption.kms.KeyManagementServiceClient")
    def test_decrypt_invalid_base64_raises_error(self, mock_kms_client):
        """Test decrypt_token raises error for invalid base64."""
        invalid_encrypted = "not_valid_base64!@#$%"

        with pytest.raises(binascii.Error):
            decrypt_token(invalid_encrypted)
