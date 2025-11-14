"""Token encryption using GCP KMS."""

import base64
import json
from typing import Any

from google.cloud import kms

from app.config import get_settings


def _get_kms_key_name() -> str:
    """Get KMS key name from settings for multi-environment support.

    Returns:
        Full KMS key resource name
    """
    settings = get_settings()
    return (
        f"projects/{settings.gcp_project_id}"
        f"/locations/{settings.gcp_region}"
        f"/keyRings/selflytics-keys"
        f"/cryptoKeys/token-encryption"
    )


def encrypt_token(token_dict: dict[str, Any]) -> str:
    """Encrypt token dictionary using KMS.

    Args:
        token_dict: Dictionary containing OAuth token data

    Returns:
        Base64-encoded ciphertext string

    Raises:
        Exception: If KMS encryption fails
    """
    kms_client = kms.KeyManagementServiceClient()

    # Serialize token to JSON
    plaintext = json.dumps(token_dict).encode("utf-8")

    # Encrypt with KMS
    kms_key_name = _get_kms_key_name()
    encrypt_response = kms_client.encrypt(request={"name": kms_key_name, "plaintext": plaintext})

    # Return base64-encoded ciphertext
    return base64.b64encode(encrypt_response.ciphertext).decode("utf-8")


def decrypt_token(encrypted_token: str) -> dict[str, Any]:
    """Decrypt token using KMS.

    Args:
        encrypted_token: Base64-encoded ciphertext string

    Returns:
        Dictionary containing decrypted OAuth token data

    Raises:
        Exception: If base64 decoding or KMS decryption fails
    """
    kms_client = kms.KeyManagementServiceClient()

    # Decode base64
    ciphertext = base64.b64decode(encrypted_token.encode("utf-8"))

    # Decrypt with KMS
    kms_key_name = _get_kms_key_name()
    decrypt_response = kms_client.decrypt(request={"name": kms_key_name, "ciphertext": ciphertext})

    # Parse JSON and return dict
    result: dict[str, Any] = json.loads(decrypt_response.plaintext.decode("utf-8"))
    return result
