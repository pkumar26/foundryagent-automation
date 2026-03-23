"""Integration tests for doc-assistant agent run lifecycle."""

import os
import time

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.doc_assistant]

# Skip all tests in this module if no endpoint
ENDPOINT = os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
if not ENDPOINT:
    pytest.skip(
        "AZURE_AI_PROJECT_ENDPOINT not set — skipping integration tests",
        allow_module_level=True,
    )


@pytest.fixture
def test_agent_name():
    """Generate a unique test agent name."""
    return f"test-doc-assistant-run-{int(time.time())}"


@pytest.fixture
def project_client():
    """Create a real AIProjectClient."""
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    return AIProjectClient(
        endpoint=ENDPOINT,
        credential=DefaultAzureCredential(),
    )


@pytest.fixture
def test_agent(project_client, test_agent_name):
    """Create a test agent version and return it; delete after test."""
    from azure.ai.projects.models import PromptAgentDefinition

    definition = PromptAgentDefinition(
        model="gpt-4o",
        instructions="You are a test agent. Always respond with 'Test OK'.",
    )
    agent = project_client.agents.create_version(
        agent_name=test_agent_name,
        definition=definition,
    )
    yield agent
    try:
        project_client.agents.delete_agent(agent_name=test_agent_name)
    except Exception:
        pass


class TestAgentRunIntegration:
    """Integration tests for the full agent run lifecycle."""

    def test_full_conversation_lifecycle(self, project_client, test_agent):
        """Should create conversation, get response, and cleanup."""
        openai_client = project_client.get_openai_client()

        # Create conversation with initial message
        conversation = openai_client.conversations.create(
            items=[{"type": "message", "role": "user", "content": "Hello!"}],
        )
        assert conversation.id is not None

        try:
            # Get agent response
            response = openai_client.responses.create(
                conversation=conversation.id,
                extra_body={
                    "agent_reference": {
                        "name": test_agent.name,
                        "type": "agent_reference",
                    }
                },
            )

            assert response.output_text is not None
            assert len(response.output_text) > 0
        finally:
            try:
                openai_client.conversations.delete(conversation_id=conversation.id)
            except Exception:
                pass
