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
def mock_openai_client():
    """Provide a fully mocked OpenAI client (conversations + responses)."""
    openai_client = MagicMock()

    # Default: conversation creation
    conversation = MagicMock()
    conversation.id = "conv-1"
    openai_client.conversations.create.return_value = conversation

    # Default: successful response with text output only
    response = MagicMock()
    response.output_text = "Hello from agent"
    text_item = MagicMock()
    text_item.type = "message"
    response.output = [text_item]
    openai_client.responses.create.return_value = response

    return openai_client


@pytest.fixture
def mock_project_client(mock_openai_client):
    """Provide a mocked AIProjectClient with OpenAI client context manager."""
    with patch("agents._base.run.get_project_client") as mock_get:
        project_client = MagicMock()
        mock_get.return_value = project_client

        # get_openai_client() returns context manager yielding the openai client
        project_client.get_openai_client.return_value.__enter__ = MagicMock(
            return_value=mock_openai_client
        )
        project_client.get_openai_client.return_value.__exit__ = MagicMock(return_value=False)

        yield project_client


class TestRunAgent:
    """Tests for the run_agent function."""

    def test_success_returns_response(self, mock_project_client, mock_openai_client):
        """Should return the agent's response text on successful run."""
        result = run_agent("https://endpoint", "test-agent", "Hello")

        assert result == "Hello from agent"
        mock_openai_client.conversations.create.assert_called_once()
        mock_openai_client.responses.create.assert_called_once()
        mock_openai_client.conversations.delete.assert_called_once_with(conversation_id="conv-1")

    def test_cleans_up_conversation_on_failure(self, mock_project_client, mock_openai_client):
        """Should delete the conversation even when an error occurs."""
        mock_openai_client.responses.create.side_effect = RuntimeError("API error")

        with pytest.raises(RuntimeError, match="API error"):
            run_agent("https://endpoint", "test-agent", "Hello")

        mock_openai_client.conversations.delete.assert_called_once_with(conversation_id="conv-1")

    def test_no_output_text_returns_empty_string(self, mock_project_client, mock_openai_client):
        """Should return empty string when output_text is None."""
        response = MagicMock()
        response.output_text = None
        response.output = []
        mock_openai_client.responses.create.return_value = response

        result = run_agent("https://endpoint", "test-agent", "Hello")

        assert result == ""

    @patch("agents._base.run._load_tool_functions")
    def test_handles_function_calls(self, mock_load_tools, mock_project_client, mock_openai_client):
        """Should execute function calls and submit results."""
        mock_load_tools.return_value = {"greet_user": lambda name: f"Hi {name}!"}

        # First response has a function_call
        func_call = MagicMock()
        func_call.type = "function_call"
        func_call.name = "greet_user"
        func_call.arguments = '{"name": "Alice"}'
        func_call.call_id = "call-1"

        response1 = MagicMock()
        response1.output = [func_call]

        # Second response has text
        text_item = MagicMock()
        text_item.type = "message"
        response2 = MagicMock()
        response2.output = [text_item]
        response2.output_text = "Greeted Alice"

        mock_openai_client.responses.create.side_effect = [response1, response2]

        result = run_agent("https://endpoint", "test-agent", "Hello")

        assert result == "Greeted Alice"
        assert mock_openai_client.responses.create.call_count == 2

    @patch("agents._base.run._load_tool_functions")
    def test_handles_unknown_function(
        self, mock_load_tools, mock_project_client, mock_openai_client
    ):
        """Should return error output for unknown function calls."""
        mock_load_tools.return_value = {}

        func_call = MagicMock()
        func_call.type = "function_call"
        func_call.name = "unknown_func"
        func_call.arguments = "{}"
        func_call.call_id = "call-1"

        response1 = MagicMock()
        response1.output = [func_call]

        text_item = MagicMock()
        text_item.type = "message"
        response2 = MagicMock()
        response2.output = [text_item]
        response2.output_text = "Function not found"

        mock_openai_client.responses.create.side_effect = [response1, response2]

        run_agent("https://endpoint", "test-agent", "Hello")

        # Assert the function_call_output was submitted
        second_call = mock_openai_client.responses.create.call_args_list[1]
        assert second_call.kwargs["input"][0]["type"] == "function_call_output"

    @patch("agents._base.run._load_tool_functions")
    def test_raises_on_max_iterations(
        self, mock_load_tools, mock_project_client, mock_openai_client
    ):
        """Should raise AgentRunError when function call loop exceeds max iterations."""
        mock_load_tools.return_value = {"loop_func": lambda: "result"}

        func_call = MagicMock()
        func_call.type = "function_call"
        func_call.name = "loop_func"
        func_call.arguments = "{}"
        func_call.call_id = "call-loop"

        looping_response = MagicMock()
        looping_response.output = [func_call]
        mock_openai_client.responses.create.return_value = looping_response

        with pytest.raises(AgentRunError, match="Maximum iterations"):
            run_agent("https://endpoint", "test-agent", "Hello")
