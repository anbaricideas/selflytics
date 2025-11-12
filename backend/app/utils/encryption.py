"""Token encryption using GCP KMS."""

import base64
import json

from google.cloud import kms


# KMS key configuration
KMS_KEY_NAME = "projects/selflytics-infra/locations/australia-southeast1/keyRings/selflytics-keys/cryptoKeys/token-encryption"


def encrypt_token(token_dict: dict) -> str:
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
    encrypt_response = kms_client.encrypt(request={"name": KMS_KEY_NAME, "plaintext": plaintext})

    # Return base64-encoded ciphertext
    return base64.b64encode(encrypt_response.ciphertext).decode("utf-8")


def decrypt_token(encrypted_token: str) -> dict:
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
    decrypt_response = kms_client.decrypt(request={"name": KMS_KEY_NAME, "ciphertext": ciphertext})

    # Parse JSON and return dict
    return json.loads(decrypt_response.plaintext.decode("utf-8"))
