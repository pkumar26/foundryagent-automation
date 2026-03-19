"""Integration tests for code-helper agent run lifecycle."""

import os
import time

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.code_helper]

# Skip all tests in this module if no connection string
CONNECTION_STRING = os.environ.get("FOUNDRY_PROJECT_CONNECTION_STRING")
if not CONNECTION_STRING:
    pytest.skip(
        "FOUNDRY_PROJECT_CONNECTION_STRING not set — skipping integration tests",
        allow_module_level=True,
    )


@pytest.fixture
def test_agent_name():
    """Generate a unique test agent name."""
    return f"test-code-helper-run-{int(time.time())}"


@pytest.fixture
def agents_client():
    """Create a real agents client."""
    from azure.ai.agents import AgentsClient
    from azure.identity import DefaultAzureCredential

    client = AgentsClient(
        endpoint=CONNECTION_STRING,
        credential=DefaultAzureCredential(),
    )
    return client


@pytest.fixture
def test_agent(agents_client, test_agent_name):
    """Create a test agent and clean up after."""
    agent = agents_client.create_agent(
        model="gpt-4o",
        name=test_agent_name,
        instructions="You are a test agent. Always respond with 'Test OK'.",
    )
    yield agent
    # Teardown
    try:
        agents_client.delete_agent(agent.id)
    except Exception:
        pass


class TestAgentRunIntegration:
    """Integration tests for the full agent run lifecycle."""

    def test_full_run_lifecycle(self, agents_client, test_agent):
        """Should create thread, post message, run agent, and get response."""
        from azure.ai.agents.models import MessageRole, RunStatus

        # Create thread
        thread = agents_client.threads.create()
        assert thread.id is not None

        try:
            # Post message
            agents_client.messages.create(
                thread_id=thread.id,
                role="user",
                content="Hello!",
            )

            # Run agent
            run = agents_client.runs.create_and_process(
                thread_id=thread.id,
                agent_id=test_agent.id,
            )

            assert run.status == RunStatus.COMPLETED

            # Get response
            last_msg = agents_client.messages.get_last_message_text_by_role(
                thread_id=thread.id,
                role=MessageRole.AGENT,
            )

            assert last_msg is not None
            assert len(last_msg.text.value) > 0
        finally:
            try:
                agents_client.threads.delete(thread.id)
            except Exception:
                pass
