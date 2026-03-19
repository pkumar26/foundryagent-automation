"""Thread-and-run lifecycle helper for agent interactions."""

from azure.ai.agents.models import MessageRole, RunStatus

from agents._base.client import get_client


class AgentRunError(Exception):
    """Raised when an agent run ends in a non-completed terminal state."""


def run_agent(
    connection_string: str,
    agent_id: str,
    prompt: str,
    timeout: int = 120,
) -> str:
    """Execute a full thread-and-run lifecycle.

    Creates a thread, posts a message, runs the agent, and retrieves the response.

    Args:
        connection_string: Foundry project endpoint URL.
        agent_id: The deployed agent's ID.
        prompt: The user message to send.
        timeout: Maximum seconds to wait for run completion.

    Returns:
        The agent's response text.

    Raises:
        AgentRunError: If the run fails or is cancelled.
        TimeoutError: If the run does not complete within the timeout.
    """
    client = get_client(connection_string)

    # Create thread
    thread = client.threads.create()

    try:
        # Send message
        client.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt,
        )

        # Create and process run (SDK handles polling)
        run = client.runs.create_and_process(
            thread_id=thread.id,
            agent_id=agent_id,
        )

        # Check terminal status
        if run.status == RunStatus.FAILED:
            error_msg = getattr(run, "last_error", None)
            raise AgentRunError(f"Agent run failed: {error_msg or 'Unknown error'}")
        if run.status == RunStatus.CANCELLED:
            raise AgentRunError("Agent run was cancelled")
        if run.status != RunStatus.COMPLETED:
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
            pass
