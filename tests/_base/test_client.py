"""Unit tests for AgentsClient singleton."""

from unittest.mock import MagicMock, patch

from agents._base.client import get_client, reset_client


class TestGetClient:
    """Tests for the singleton client initialisation."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_client()

    def teardown_method(self):
        """Reset singleton after each test."""
        reset_client()

    @patch("agents._base.client.DefaultAzureCredential")
    @patch("agents._base.client.AgentsClient")
    def test_creates_client_with_endpoint(self, mock_client_cls, mock_cred_cls):
        """Client should be created with endpoint and credential."""
        mock_cred = MagicMock()
        mock_cred_cls.return_value = mock_cred
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        result = get_client("https://my-project.services.ai.azure.com/api/projects/myproject")

        mock_client_cls.assert_called_once_with(
            endpoint="https://my-project.services.ai.azure.com/api/projects/myproject",
            credential=mock_cred,
        )
        assert result is mock_client

    @patch("agents._base.client.DefaultAzureCredential")
    @patch("agents._base.client.AgentsClient")
    def test_returns_singleton(self, mock_client_cls, mock_cred_cls):
        """Subsequent calls should return the same client instance."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        client1 = get_client("https://endpoint")
        client2 = get_client("https://endpoint")

        assert client1 is client2
        assert mock_client_cls.call_count == 1

    def test_reset_client_clears_singleton(self):
        """reset_client should clear the cached instance."""
        with patch("agents._base.client.AgentsClient") as mock_cls:
            with patch("agents._base.client.DefaultAzureCredential"):
                mock_cls.return_value = MagicMock()

                get_client("https://endpoint")
                reset_client()
                get_client("https://endpoint-2")

                assert mock_cls.call_count == 2
