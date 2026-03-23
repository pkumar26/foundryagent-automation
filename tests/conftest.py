"""Root conftest — shared fixtures and marker registration."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_config():
    """Create a mock FoundryBaseConfig-like object for testing."""
    config = MagicMock()
    config.azure_ai_project_endpoint = "https://test-endpoint.services.ai.azure.com"
    config.environment = "dev"
    config.azure_key_vault_name = "test-kv"
    config.agent_name = "test-agent"
    config.agent_model = "gpt-4o"
    config.agent_instructions_path = "agents/code_helper/instructions.md"
    config.knowledge_source_enabled = False
    return config


@pytest.fixture
def mock_client():
    """Create a mock AIProjectClient."""
    with patch("agents._base.client.AIProjectClient") as mock_cls:
        project_client = MagicMock()
        mock_cls.return_value = project_client
        yield project_client


@pytest.fixture
def mock_agents_client(mock_client):
    """Create a mock agents client (same as mock_client)."""
    return mock_client
