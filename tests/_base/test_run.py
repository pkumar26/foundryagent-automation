"""Unit tests for run_agent lifecycle and AgentRunError."""

from unittest.mock import MagicMock, patch

import pytest

from agents._base.run import AgentRunError, run_agent


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset the client singleton before and after each test."""
    from agents._base.client import reset_client

    reset_client()
    yield
    reset_client()


@pytest.fixture
def mock_client():
    """Provide a fully mocked AgentsClient."""
    with patch("agents._base.run.get_client") as mock_get:
        client = MagicMock()
        mock_get.return_value = client

        # Default: thread creation
        thread = MagicMock()
        thread.id = "thread-1"
        client.threads.create.return_value = thread

        # Default: successful run
        run = MagicMock()
        run.status = "completed"
        client.runs.create_and_process.return_value = run

        # Default: response message
        msg = MagicMock()
        msg.text.value = "Hello from agent"
        client.messages.get_last_message_text_by_role.return_value = msg

        yield client


class TestRunAgent:
    """Tests for the run_agent function."""

    def test_success_returns_response(self, mock_client):
        """Should return the agent's response text on successful run."""
        result = run_agent("conn-str", "agent-1", "Hello")

        assert result == "Hello from agent"
        mock_client.threads.create.assert_called_once()
        mock_client.messages.create.assert_called_once()
        mock_client.runs.create_and_process.assert_called_once()
        mock_client.threads.delete.assert_called_once_with("thread-1")

    def test_failed_run_raises_agent_run_error(self, mock_client):
        """Should raise AgentRunError when run status is 'failed'."""
        run = MagicMock()
        run.status = "failed"
        run.last_error = "Model overloaded"
        mock_client.runs.create_and_process.return_value = run

        with pytest.raises(AgentRunError, match="Agent run failed"):
            run_agent("conn-str", "agent-1", "Hello")

    def test_cancelled_run_raises_agent_run_error(self, mock_client):
        """Should raise AgentRunError when run status is 'cancelled'."""
        run = MagicMock()
        run.status = "cancelled"
        mock_client.runs.create_and_process.return_value = run

        with pytest.raises(AgentRunError, match="cancelled"):
            run_agent("conn-str", "agent-1", "Hello")

    def test_unexpected_status_raises_agent_run_error(self, mock_client):
        """Should raise AgentRunError for unexpected terminal status."""
        run = MagicMock()
        run.status = "expired"
        mock_client.runs.create_and_process.return_value = run

        with pytest.raises(AgentRunError, match="unexpected status"):
            run_agent("conn-str", "agent-1", "Hello")

    def test_cleans_up_thread_on_failure(self, mock_client):
        """Should delete the thread even when the run fails."""
        run = MagicMock()
        run.status = "failed"
        run.last_error = "Error"
        mock_client.runs.create_and_process.return_value = run

        with pytest.raises(AgentRunError):
            run_agent("conn-str", "agent-1", "Hello")

        mock_client.threads.delete.assert_called_once_with("thread-1")

    def test_no_response_returns_empty_string(self, mock_client):
        """Should return empty string when no agent message is found."""
        mock_client.messages.get_last_message_text_by_role.return_value = None

        result = run_agent("conn-str", "agent-1", "Hello")

        assert result == ""

    @patch("agents._base.run._register_agent_tools")
    def test_registers_tools_when_agent_name_provided(self, mock_register, mock_client):
        """Should register tools when agent_name is provided."""
        run_agent("conn-str", "agent-1", "Hello", agent_name="code-helper")

        mock_register.assert_called_once_with(mock_client, "code-helper")

    @patch("agents._base.run._register_agent_tools")
    def test_skips_tool_registration_when_no_agent_name(self, mock_register, mock_client):
        """Should not register tools when agent_name is None."""
        run_agent("conn-str", "agent-1", "Hello")

        mock_register.assert_not_called()
