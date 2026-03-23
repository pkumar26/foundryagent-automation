# Quickstart: Migrate to New Foundry SDK

**Feature**: 005-migrate-to-new-foundry
**Date**: 2026-03-22

## Prerequisites

- Python 3.11+
- Azure AI Foundry project (new resource model, not Hub+Project)
- Azure CLI installed and authenticated (`az login`)
- Project endpoint URL (format: `https://<account>.services.ai.azure.com/api/projects/<project-name>`)

## Step 1: Update Dependencies

```bash
# Install all dependencies from pyproject.toml
uv sync
```

## Step 2: Update Environment Variables

Rename `FOUNDRY_PROJECT_CONNECTION_STRING` to `AZURE_AI_PROJECT_ENDPOINT` in your `.env`:

```bash
# Old (remove):
# FOUNDRY_PROJECT_CONNECTION_STRING=https://...

# New:
AZURE_AI_PROJECT_ENDPOINT=https://your-account.services.ai.azure.com/api/projects/your-project
```

The endpoint URL can be found in the Microsoft Foundry portal under your Project's Overview page.

## Step 3: Verify Connection

```python
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

project_client = AIProjectClient(
    endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential()
)
print("Connected to Azure AI Foundry")
```

## Step 4: Deploy an Agent

```python
from agents.registry import REGISTRY

entry = REGISTRY.get_agent("code-helper")
config = entry.config_class()
agent = entry.factory(config)
print(f"Agent ready: {agent.name} v{agent.version} (id: {agent.id})")
```

## Step 5: Run a Conversation

```python
with project_client.get_openai_client() as openai_client:
    # Create conversation
    conversation = openai_client.conversations.create(
        items=[{"type": "message", "role": "user", "content": "Hello! What can you help me with?"}],
    )

    # Get response
    response = openai_client.responses.create(
        conversation=conversation.id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
    )
    print(response.output_text)

    # Cleanup
    openai_client.conversations.delete(conversation_id=conversation.id)
```

## Step 6: Run Tests

```bash
# Unit tests (no Azure credentials needed)
pytest tests/ -m "not integration" -v

# Integration tests (requires AZURE_AI_PROJECT_ENDPOINT)
pytest tests/ -m integration -v
```

## Key Differences from Old SDK

| What Changed | Old | New |
|-------------|-----|-----|
| Package | `azure-ai-agents` | `azure-ai-projects>=2.0.0` |
| Client | `AgentsClient(endpoint=..., credential=...)` | `AIProjectClient(endpoint=..., credential=...)` |
| Env var | `FOUNDRY_PROJECT_CONNECTION_STRING` | `AZURE_AI_PROJECT_ENDPOINT` |
| Create agent | `client.create_agent(model, name, instructions, tools)` | `client.agents.create_version(agent_name, definition=PromptAgentDefinition(...))` |
| Thread | `client.threads.create()` | `openai_client.conversations.create(items=[...])` |
| Message | `client.messages.create(thread_id, role, content)` | Via conversation items |
| Run | `client.runs.create_and_process(thread_id, agent_id)` | `openai_client.responses.create(conversation=id, extra_body={...})` |
| Get response | `client.messages.get_last_message_text_by_role()` | `response.output_text` |
| Tool def | `FunctionTool(functions=[callable])` | `FunctionTool(name=..., parameters={schema}, description=...)` |
| Delete thread | `client.threads.delete(thread_id)` | `openai_client.conversations.delete(conversation_id=id)` |
