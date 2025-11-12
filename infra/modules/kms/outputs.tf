output "key_ring_id" {
  description = "ID of the KMS key ring"
  value       = google_kms_key_ring.key_ring.id
}

output "key_ring_name" {
  description = "Name of the KMS key ring"
  value       = google_kms_key_ring.key_ring.name
}

output "crypto_key_id" {
  description = "ID of the token encryption crypto key"
  value       = google_kms_crypto_key.token_encryption.id
}

output "crypto_key_name" {
  description = "Full resource name of the token encryption crypto key"
  value       = google_kms_crypto_key.token_encryption.name
}
