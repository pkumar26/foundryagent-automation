"""Root conftest — shared fixtures and marker registration."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_config():
    """Create a mock FoundryBaseConfig-like object for testing."""
    config = MagicMock()
    config.foundry_project_connection_string = "test-connection-string"
    config.environment = "dev"
    config.azure_key_vault_name = "test-kv"
    config.agent_name = "test-agent"
    config.agent_model = "gpt-4o"
    config.agent_instructions_path = "agents/code_helper/instructions.md"
    config.knowledge_source_enabled = False
    config.github_mcp_enabled = False
    return config


@pytest.fixture
def mock_client():
    """Create a mock AgentsClient."""
    with patch("agents._base.client.AgentsClient") as mock_cls:
        client = MagicMock()
        mock_cls.return_value = client
        yield client


@pytest.fixture
def mock_agents_client(mock_client):
    """Create a mock agents client (same as mock_client in v2.0 SDK)."""
    return mock_client
