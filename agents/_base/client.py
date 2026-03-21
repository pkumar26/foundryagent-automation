"""Singleton AgentsClient initialisation using DefaultAzureCredential."""

import logging

from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

_client: AgentsClient | None = None
_endpoint: str | None = None


def get_client(endpoint: str) -> AgentsClient:
    """Get or create a singleton AgentsClient.

    Args:
        endpoint: Azure AI Foundry project endpoint URL.

    Returns:
        A shared AgentsClient instance.

    Raises:
        ValueError: If called with a different endpoint than the existing client.
    """
    global _client, _endpoint
    if _client is not None and _endpoint != endpoint:
        raise ValueError(
            f"Client already initialized with endpoint '{_endpoint}'. "
            f"Cannot reinitialize with '{endpoint}'. Call reset_client() first."
        )
    if _client is None:
        logger.info("Creating AgentsClient for endpoint: %s", endpoint)
        _client = AgentsClient(
            endpoint=endpoint,
            credential=DefaultAzureCredential(),
        )
        _endpoint = endpoint
    return _client


def reset_client() -> None:
    """Reset the singleton client. Used for testing."""
    global _client, _endpoint
    _client = None
    _endpoint = None
