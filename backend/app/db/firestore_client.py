"""Firestore database client for Selflytics."""

from functools import lru_cache

from google.cloud import firestore


@lru_cache
def get_firestore_client() -> firestore.Client:
    """Get cached Firestore client instance.

    Returns:
        Firestore client configured with project settings from environment.

    Note:
        This function is cached to ensure a single client instance is reused
        across the application lifetime, improving performance and connection pooling.
    """
    return firestore.Client()
