"""Unit tests for create_or_update_agent factory."""

from unittest.mock import MagicMock, patch

import pytest

from agents._base.agent_factory import create_or_update_agent


@pytest.fixture
def agent_config(tmp_path):
    """Create a mock config with a real instructions file."""
    instructions_file = tmp_path / "instructions.md"
    instructions_file.write_text("You are a helpful agent.")

    config = MagicMock()
    config.foundry_project_connection_string = "test-conn-str"
    config.agent_name = "test-agent"
    config.agent_model = "gpt-4o"
    config.agent_instructions_path = str(instructions_file)
    config.knowledge_source_enabled = False
    config.code_interpreter_enabled = False
    return config


@pytest.fixture
def mock_agents_client():
    """Create a mock agents client."""
    client = MagicMock()
    # Default: no existing agents
    client.list_agents.return_value = []
    return client


class TestCreateOrUpdateAgent:
    """Tests for the agent factory function."""

    @patch("agents._base.agent_factory._collect_agent_tools", return_value=[])
    @patch("agents._base.agent_factory.get_client")
    def test_creates_new_agent(self, mock_get_client, mock_tools, agent_config):
        """Should create a new agent when none exists with the name."""
        mock_client = MagicMock()
        mock_client.list_agents.return_value = []
        mock_get_client.return_value = mock_client

        created_agent = MagicMock()
        created_agent.id = "agent-123"
        mock_client.create_agent.return_value = created_agent

        result = create_or_update_agent(agent_config)

        mock_client.create_agent.assert_called_once()
        assert result is created_agent

    @patch("agents._base.agent_factory._collect_agent_tools", return_value=[])
    @patch("agents._base.agent_factory.get_client")
    def test_updates_existing_agent(self, mock_get_client, mock_tools, agent_config):
        """Should update an existing agent when one with the same name exists."""
        existing_agent = MagicMock()
        existing_agent.id = "agent-existing"
        existing_agent.name = "test-agent"

        mock_client = MagicMock()
        mock_client.list_agents.return_value = [existing_agent]
        mock_get_client.return_value = mock_client

        updated_agent = MagicMock()
        updated_agent.id = "agent-existing"
        mock_client.update_agent.return_value = updated_agent

        result = create_or_update_agent(agent_config)

        mock_client.update_agent.assert_called_once()
        call_kwargs = mock_client.update_agent.call_args
        assert call_kwargs.kwargs["agent_id"] == "agent-existing"
        assert result is updated_agent

    def test_missing_instructions_raises_file_not_found(self, agent_config):
        """Should raise FileNotFoundError when instructions file doesn't exist."""
        agent_config.agent_instructions_path = "/nonexistent/path/instructions.md"

        with pytest.raises(FileNotFoundError, match="Instructions file not found"):
            create_or_update_agent(agent_config)

    def test_empty_instructions_raises_value_error(self, agent_config, tmp_path):
        """Should raise ValueError when instructions file is empty."""
        empty_file = tmp_path / "empty.md"
        empty_file.write_text("   ")
        agent_config.agent_instructions_path = str(empty_file)

        with pytest.raises(ValueError, match="Instructions file is empty"):
            create_or_update_agent(agent_config)

    @patch("agents._base.agent_factory._collect_agent_tools", return_value=[])
    @patch("agents._base.agent_factory.get_client")
    def test_conditional_knowledge_tool_not_appended_when_disabled(
        self, mock_get_client, mock_tools, agent_config
    ):
        """Should not append knowledge tool when disabled."""
        agent_config.knowledge_source_enabled = False

        mock_client = MagicMock()
        mock_client.list_agents.return_value = []
        mock_client.create_agent.return_value = MagicMock(id="agent-new")
        mock_get_client.return_value = mock_client

        create_or_update_agent(agent_config)

        # Verify tools passed to create_agent are empty (no knowledge tool)
        call_kwargs = mock_client.create_agent.call_args
        assert call_kwargs.kwargs["tools"] == []

    @patch("agents._base.agent_factory._collect_agent_tools", return_value=[])
    @patch("agents._base.agent_factory.get_client")
    def test_idempotent_multiple_calls(self, mock_get_client, mock_tools, agent_config):
        """Running create_or_update multiple times should produce same state."""
        mock_client = MagicMock()

        # First call: no existing agent
        # Second call: agent now exists
        existing = MagicMock()
        existing.id = "agent-123"
        existing.name = "test-agent"

        mock_client.list_agents.side_effect = [[], [existing]]
        mock_client.create_agent.return_value = MagicMock(id="agent-123")
        mock_client.update_agent.return_value = MagicMock(id="agent-123")
        mock_get_client.return_value = mock_client

        # First call creates
        create_or_update_agent(agent_config)
        mock_client.create_agent.assert_called_once()

        # Second call updates
        create_or_update_agent(agent_config)
        mock_client.update_agent.assert_called_once()
