/**
 * KMS Module
 *
 * Creates KMS key ring and crypto key for token encryption.
 */

resource "google_kms_key_ring" "key_ring" {
  name     = "${var.project_name}-keys"
  location = var.region
  project  = var.project_id
}

resource "google_kms_crypto_key" "token_encryption" {
  name            = "token-encryption"
  key_ring        = google_kms_key_ring.key_ring.id
  rotation_period = "7776000s" # 90 days

  lifecycle {
    prevent_destroy = true
  }
}

# IAM binding for Cloud Run service account
resource "google_kms_crypto_key_iam_member" "cloud_run_encrypt_decrypt" {
  crypto_key_id = google_kms_crypto_key.token_encryption.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${var.cloud_run_service_account}"
}
