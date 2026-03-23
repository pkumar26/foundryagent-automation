"""Singleton AIProjectClient initialisation using DefaultAzureCredential."""

import logging
import threading

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_client: AIProjectClient | None = None
_endpoint: str | None = None


def get_project_client(endpoint: str) -> AIProjectClient:
    """Get or create a singleton AIProjectClient.

    Args:
        endpoint: Azure AI Project endpoint URL.

    Returns:
        A shared AIProjectClient instance.

    Raises:
        ValueError: If called with a different endpoint than the existing client.
    """
    global _client, _endpoint
    with _lock:
        if _client is not None and _endpoint != endpoint:
            raise ValueError(
                f"Client already initialized with endpoint '{_endpoint}'. "
                f"Cannot reinitialize with '{endpoint}'. Call reset_client() first."
            )
        if _client is None:
            logger.info("Creating AIProjectClient for endpoint: %s", endpoint)
            _client = AIProjectClient(
                endpoint=endpoint,
                credential=DefaultAzureCredential(),
            )
            _endpoint = endpoint
        return _client


def reset_client() -> None:
    """Reset the singleton client. Used for testing."""
    global _client, _endpoint
    with _lock:
        _client = None
        _endpoint = None
