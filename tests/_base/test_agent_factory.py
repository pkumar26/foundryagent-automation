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
    config.azure_ai_project_endpoint = "https://test-endpoint.services.ai.azure.com"
    config.agent_name = "test-agent"
    config.agent_model = "gpt-4o"
    config.agent_instructions_path = str(instructions_file)
    config.knowledge_source_enabled = False
    config.code_interpreter_enabled = False
    config.web_search_enabled = False
    config.github_enabled = False
    config.github_project_connection_id = ""
    return config


@pytest.fixture
def mock_project_client():
    """Create a mock project client with agents sub-client."""
    client = MagicMock()
    return client


class TestCreateOrUpdateAgent:
    """Tests for the agent factory function."""

    @patch("agents._base.agent_factory._collect_agent_tools", return_value=[])
    @patch("agents._base.agent_factory.get_project_client")
    def test_creates_agent_version(self, mock_get_client, mock_tools, agent_config):
        """Should create a new agent version via create_version."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        agent_version = MagicMock()
        agent_version.id = "agent-123"
        agent_version.name = "test-agent"
        agent_version.version = "1"
        mock_client.agents.create_version.return_value = agent_version

        result = create_or_update_agent(agent_config)

        mock_client.agents.create_version.assert_called_once()
        call_kwargs = mock_client.agents.create_version.call_args
        assert call_kwargs.kwargs["agent_name"] == "test-agent"
        assert result is agent_version

    @patch("agents._base.agent_factory._collect_agent_tools", return_value=[])
    @patch("agents._base.agent_factory.get_project_client")
    def test_passes_prompt_agent_definition(self, mock_get_client, mock_tools, agent_config):
        """Should construct PromptAgentDefinition with correct model/instructions."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.agents.create_version.return_value = MagicMock(id="agent-123")

        create_or_update_agent(agent_config)

        call_kwargs = mock_client.agents.create_version.call_args
        definition = call_kwargs.kwargs["definition"]
        assert definition.model == "gpt-4o"
        assert definition.instructions == "You are a helpful agent."

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
    @patch("agents._base.agent_factory.get_project_client")
    def test_conditional_knowledge_tool_not_appended_when_disabled(
        self, mock_get_client, mock_tools, agent_config
    ):
        """Should not append knowledge tool when disabled."""
        agent_config.knowledge_source_enabled = False

        mock_client = MagicMock()
        mock_client.agents.create_version.return_value = MagicMock(id="agent-new")
        mock_get_client.return_value = mock_client

        create_or_update_agent(agent_config)

        # Verify definition tools are empty (no knowledge tool)
        call_kwargs = mock_client.agents.create_version.call_args
        definition = call_kwargs.kwargs["definition"]
        assert definition.tools == []

    @patch("agents._base.agent_factory._collect_agent_tools", return_value=[])
    @patch("agents._base.agent_factory.get_project_client")
    def test_idempotent_multiple_calls(self, mock_get_client, mock_tools, agent_config):
        """Running create_or_update multiple times should call create_version each time."""
        mock_client = MagicMock()
        mock_client.agents.create_version.return_value = MagicMock(id="agent-123")
        mock_get_client.return_value = mock_client

        # First call
        create_or_update_agent(agent_config)
        # Second call
        create_or_update_agent(agent_config)

        assert mock_client.agents.create_version.call_count == 2

    @patch("agents._base.agent_factory._collect_agent_tools", return_value=[])
    @patch("agents._base.agent_factory.get_project_client")
    def test_github_mcp_not_appended_when_disabled(self, mock_get_client, mock_tools, agent_config):
        """Should not append GitHub MCP tool when disabled."""
        agent_config.github_enabled = False

        mock_client = MagicMock()
        mock_client.agents.create_version.return_value = MagicMock(id="agent-new")
        mock_get_client.return_value = mock_client

        create_or_update_agent(agent_config)

        call_kwargs = mock_client.agents.create_version.call_args
        definition = call_kwargs.kwargs["definition"]
        assert definition.tools == []

    @patch("agents._base.agent_factory._collect_agent_tools", return_value=[])
    @patch("agents._base.agent_factory.get_project_client")
    def test_code_interpreter_appended_when_enabled(
        self, mock_get_client, mock_tools, agent_config
    ):
        """Should append CodeInterpreterTool when enabled."""
        agent_config.code_interpreter_enabled = True

        mock_client = MagicMock()
        mock_client.agents.create_version.return_value = MagicMock(id="agent-new")
        mock_get_client.return_value = mock_client

        create_or_update_agent(agent_config)

        call_kwargs = mock_client.agents.create_version.call_args
        definition = call_kwargs.kwargs["definition"]
        assert len(definition.tools) == 1
        assert type(definition.tools[0]).__name__ == "CodeInterpreterTool"

    @patch("agents._base.agent_factory._collect_agent_tools", return_value=[])
    @patch("agents._base.agent_factory.get_project_client")
    def test_web_search_not_appended_when_disabled(self, mock_get_client, mock_tools, agent_config):
        """Should not append WebSearchTool when disabled."""
        agent_config.web_search_enabled = False

        mock_client = MagicMock()
        mock_client.agents.create_version.return_value = MagicMock(id="agent-new")
        mock_get_client.return_value = mock_client

        create_or_update_agent(agent_config)

        call_kwargs = mock_client.agents.create_version.call_args
        definition = call_kwargs.kwargs["definition"]
        assert definition.tools == []

    @patch("agents._base.agent_factory._collect_agent_tools", return_value=[])
    @patch("agents._base.agent_factory.get_project_client")
    def test_web_search_appended_when_enabled(self, mock_get_client, mock_tools, agent_config):
        """Should append WebSearchTool when enabled."""
        agent_config.web_search_enabled = True

        mock_client = MagicMock()
        mock_client.agents.create_version.return_value = MagicMock(id="agent-new")
        mock_get_client.return_value = mock_client

        create_or_update_agent(agent_config)

        call_kwargs = mock_client.agents.create_version.call_args
        definition = call_kwargs.kwargs["definition"]
        assert len(definition.tools) == 1
        assert type(definition.tools[0]).__name__ == "WebSearchTool"

    @patch("agents._base.agent_factory._collect_agent_tools", return_value=[])
    @patch("agents._base.agent_factory.get_project_client")
    def test_github_mcp_appended_when_enabled(self, mock_get_client, mock_tools, agent_config):
        """Should append GitHub MCP tool when enabled with a connection ID."""
        agent_config.github_enabled = True
        agent_config.github_project_connection_id = "conn-github-123"

        mock_client = MagicMock()
        mock_client.agents.create_version.return_value = MagicMock(id="agent-new")
        mock_get_client.return_value = mock_client

        create_or_update_agent(agent_config)

        call_kwargs = mock_client.agents.create_version.call_args
        definition = call_kwargs.kwargs["definition"]
        assert len(definition.tools) == 1
        mcp_tool = definition.tools[0]
        assert mcp_tool.server_label == "github"
        assert mcp_tool.server_url == "https://api.githubcopilot.com/mcp"
        assert mcp_tool.project_connection_id == "conn-github-123"

    @patch("agents._base.agent_factory._collect_agent_tools", return_value=[])
    @patch("agents._base.agent_factory.get_project_client")
    def test_github_mcp_skipped_when_connection_id_empty(
        self, mock_get_client, mock_tools, agent_config
    ):
        """Should skip GitHub MCP tool when enabled but connection ID is empty."""
        agent_config.github_enabled = True
        agent_config.github_project_connection_id = ""

        mock_client = MagicMock()
        mock_client.agents.create_version.return_value = MagicMock(id="agent-new")
        mock_get_client.return_value = mock_client

        create_or_update_agent(agent_config)

        call_kwargs = mock_client.agents.create_version.call_args
        definition = call_kwargs.kwargs["definition"]
        assert definition.tools == []
