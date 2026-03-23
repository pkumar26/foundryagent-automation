"""Integration tests for code-helper agent creation and update."""

import os
import time

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.code_helper]

# Skip all tests in this module if no endpoint
ENDPOINT = os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
if not ENDPOINT:
    pytest.skip(
        "AZURE_AI_PROJECT_ENDPOINT not set — skipping integration tests",
        allow_module_level=True,
    )


@pytest.fixture
def test_agent_name():
    """Generate a unique test agent name with prefix and timestamp."""
    return f"test-code-helper-{int(time.time())}"


@pytest.fixture
def project_client():
    """Create a real AIProjectClient for integration testing."""
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    return AIProjectClient(
        endpoint=ENDPOINT,
        credential=DefaultAzureCredential(),
    )


class TestAgentCreateIntegration:
    """Integration tests for agent creation against live Foundry."""

    def test_create_agent_version(self, project_client, test_agent_name):
        """Should create a new agent version in Foundry."""
        from azure.ai.projects.models import PromptAgentDefinition

        definition = PromptAgentDefinition(
            model="gpt-4o",
            instructions="You are a test agent.",
        )
        agent = project_client.agents.create_version(
            agent_name=test_agent_name,
            definition=definition,
        )
        assert agent.id is not None
        assert agent.name == test_agent_name

    def test_idempotent_create_version(self, project_client, test_agent_name):
        """Should create new versions without duplicating agents."""
        from azure.ai.projects.models import PromptAgentDefinition

        definition1 = PromptAgentDefinition(
            model="gpt-4o",
            instructions="Original instructions.",
        )
        agent1 = project_client.agents.create_version(
            agent_name=test_agent_name,
            definition=definition1,
        )

        definition2 = PromptAgentDefinition(
            model="gpt-4o",
            instructions="Updated instructions.",
        )
        agent2 = project_client.agents.create_version(
            agent_name=test_agent_name,
            definition=definition2,
        )

        assert agent2.name == agent1.name
