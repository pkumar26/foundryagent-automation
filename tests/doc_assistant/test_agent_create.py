"""Integration tests for doc-assistant agent creation and update."""

import os
import time

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.doc_assistant]

# Skip all tests in this module if no connection string
CONNECTION_STRING = os.environ.get("FOUNDRY_PROJECT_CONNECTION_STRING")
if not CONNECTION_STRING:
    pytest.skip(
        "FOUNDRY_PROJECT_CONNECTION_STRING not set — skipping integration tests",
        allow_module_level=True,
    )


@pytest.fixture
def test_agent_name():
    """Generate a unique test agent name with prefix and timestamp."""
    return f"test-doc-assistant-{int(time.time())}"


@pytest.fixture
def agents_client():
    """Create a real AgentsClient for integration testing."""
    from azure.ai.agents import AgentsClient
    from azure.identity import DefaultAzureCredential

    client = AgentsClient(
        endpoint=CONNECTION_STRING,
        credential=DefaultAzureCredential(),
    )
    return client


@pytest.fixture
def cleanup_agent(agents_client, test_agent_name):
    """Fixture that yields and then cleans up the test agent."""
    yield
    # Teardown: find and delete test agent
    try:
        for agent in agents_client.list_agents():
            if agent.name == test_agent_name:
                agents_client.delete_agent(agent.id)
                break
    except Exception:
        pass


class TestAgentCreateIntegration:
    """Integration tests for agent creation against live Foundry."""

    def test_create_agent(self, agents_client, test_agent_name, cleanup_agent):
        """Should create a new agent in Foundry."""
        agent = agents_client.create_agent(
            model="gpt-4o",
            name=test_agent_name,
            instructions="You are a test agent.",
        )
        assert agent.id is not None
        assert agent.name == test_agent_name

    def test_idempotent_update(self, agents_client, test_agent_name, cleanup_agent):
        """Should update an existing agent without creating a duplicate."""
        # Create
        agent1 = agents_client.create_agent(
            model="gpt-4o",
            name=test_agent_name,
            instructions="Original instructions.",
        )

        # Update
        agent2 = agents_client.update_agent(
            agent_id=agent1.id,
            model="gpt-4o",
            name=test_agent_name,
            instructions="Updated instructions.",
        )

        assert agent2.id == agent1.id
        assert agent2.instructions == "Updated instructions."
