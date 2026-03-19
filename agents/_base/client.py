"""Singleton AgentsClient initialisation using DefaultAzureCredential."""

from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential

_client: AgentsClient | None = None


def get_client(endpoint: str) -> AgentsClient:
    """Get or create a singleton AgentsClient.

    Args:
        endpoint: Azure AI Foundry project endpoint URL.

    Returns:
        A shared AgentsClient instance.
    """
    global _client
    if _client is None:
        _client = AgentsClient(
            endpoint=endpoint,
            credential=DefaultAzureCredential(),
        )
    return _client


def reset_client() -> None:
    """Reset the singleton client. Used for testing."""
    global _client
    _client = None
