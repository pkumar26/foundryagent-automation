"""Thread-and-run lifecycle helper for agent interactions."""

import importlib
import logging

from azure.ai.agents.models import MessageRole

from agents._base.client import get_client

logger = logging.getLogger(__name__)


class AgentRunError(Exception):
    """Raised when an agent run ends in a non-completed terminal state."""


def run_agent(
    connection_string: str,
    agent_id: str,
    prompt: str,
    agent_name: str | None = None,
) -> str:
    """Execute a full thread-and-run lifecycle.

    Creates a thread, posts a message, runs the agent, and retrieves the response.

    Args:
        connection_string: Foundry project endpoint URL.
        agent_id: The deployed agent's ID.
        prompt: The user message to send.
        agent_name: Agent name (e.g. "code-helper") to load tools for auto-execution.

    Returns:
        The agent's response text.

    Raises:
        AgentRunError: If the run fails or is cancelled.
    """
    client = get_client(connection_string)

    # Register tool functions for auto-execution if agent_name is provided
    if agent_name:
        _register_agent_tools(client, agent_name)

    # Create thread
    thread = client.threads.create()
    logger.info("Created thread %s for agent %s", thread.id, agent_id)

    try:
        # Send message
        client.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt,
        )

        # Create and process run (SDK handles polling + tool execution)
        run = client.runs.create_and_process(
            thread_id=thread.id,
            agent_id=agent_id,
            polling_interval=1,
        )

        # Check terminal status
        if run.status == "failed":
            error_msg = getattr(run, "last_error", None)
            raise AgentRunError(f"Agent run failed: {error_msg or 'Unknown error'}")
        if run.status == "cancelled":
            raise AgentRunError("Agent run was cancelled")
        if run.status != "completed":
            raise AgentRunError(f"Agent run ended with unexpected status: {run.status}")

        # Retrieve last assistant message
        last_msg = client.messages.get_last_message_text_by_role(
            thread_id=thread.id,
            role=MessageRole.AGENT,
        )

        return last_msg.text.value if last_msg else ""
    finally:
        # Cleanup thread
        try:
            client.threads.delete(thread.id)
        except Exception:
            logger.warning("Failed to delete thread %s", thread.id)


def _register_agent_tools(client, agent_name: str) -> None:
    """Load and register an agent's tool functions for auto-execution."""
    module_name = agent_name.replace("-", "_")
    try:
        tools_module = importlib.import_module(f"agents.{module_name}.tools")
    except ModuleNotFoundError:
        return
    if hasattr(tools_module, "TOOLS"):
        for tool in tools_module.TOOLS:
            client.enable_auto_function_calls(tool)
