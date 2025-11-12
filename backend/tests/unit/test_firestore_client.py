"""Unit tests for Firestore client."""

from unittest.mock import MagicMock, patch

import pytest

from app.db.firestore_client import get_firestore_client


class TestFirestoreClient:
    """Test Firestore client initialization and caching."""

    def test_get_firestore_client_returns_client(self):
        """Test that get_firestore_client returns a Firestore client instance."""
        with patch("app.db.firestore_client.firestore.Client") as mock_client:
            # Configure mock to return a mock client instance
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            # Clear cache to ensure fresh call
            get_firestore_client.cache_clear()

            client = get_firestore_client()

            # Verify client was instantiated
            assert client is not None
            assert client == mock_instance
            mock_client.assert_called_once()

    def test_get_firestore_client_is_cached(self):
        """Test that get_firestore_client caches the client instance."""
        with patch("app.db.firestore_client.firestore.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            # Clear cache before test
            get_firestore_client.cache_clear()

            # Call twice
            client1 = get_firestore_client()
            client2 = get_firestore_client()

            # Should return same instance
            assert client1 is client2
            # Client should only be instantiated once (cached)
            mock_client.assert_called_once()

    def test_get_firestore_client_singleton_pattern(self):
        """Test that multiple calls return the same cached instance."""
        with patch("app.db.firestore_client.firestore.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            get_firestore_client.cache_clear()

            # Call multiple times
            clients = [get_firestore_client() for _ in range(5)]

            # All should be the same instance
            assert all(client is clients[0] for client in clients)
            # Client instantiated only once
            mock_client.assert_called_once()

    def test_get_firestore_client_with_project_config(self):
        """Test that Firestore client uses project configuration."""
        with patch("app.db.firestore_client.firestore.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            get_firestore_client.cache_clear()

            client = get_firestore_client()

            # Verify client was created (configuration passed implicitly)
            assert client is not None
            # Firestore.Client() should pick up config from environment
            mock_client.assert_called_once_with()

    def test_cache_clear_allows_new_instance(self):
        """Test that clearing cache allows getting a new client instance."""
        with patch("app.db.firestore_client.firestore.Client") as mock_client:
            mock_instance1 = MagicMock()
            mock_instance2 = MagicMock()
            mock_client.side_effect = [mock_instance1, mock_instance2]

            get_firestore_client.cache_clear()

            # Get first client
            client1 = get_firestore_client()
            assert client1 is mock_instance1

            # Clear cache
            get_firestore_client.cache_clear()

            # Get new client
            client2 = get_firestore_client()
            assert client2 is mock_instance2
            assert client1 is not client2

    @patch("app.db.firestore_client.firestore.Client")
    def test_firestore_client_error_handling(self, mock_client):
        """Test that errors from Firestore client are propagated."""
        # Configure mock to raise an error
        mock_client.side_effect = RuntimeError("Failed to connect to Firestore")

        get_firestore_client.cache_clear()

        # Should propagate the error
        with pytest.raises(RuntimeError, match="Failed to connect to Firestore"):
            get_firestore_client()
