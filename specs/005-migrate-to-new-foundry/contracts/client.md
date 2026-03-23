# Contract: Client Singleton

**Feature**: 005-migrate-to-new-foundry
**Module**: `agents/_base/client.py`

## Public API

### `get_project_client(endpoint: str) -> AIProjectClient`

Returns a singleton `AIProjectClient` instance. Creates on first call; returns cached on subsequent calls. Raises `ValueError` if called again with a different endpoint.

**Parameters**:
- `endpoint` (str): Azure AI Project endpoint URL (`https://<account>.services.ai.azure.com/api/projects/<project>`)

**Returns**: `AIProjectClient` — authenticated project client

**Side Effects**: Initializes `DefaultAzureCredential` and `AIProjectClient` on first call

**Error Cases**:
- `ValueError` if called with a different endpoint than the initial call

### `reset_client() -> None`

Resets the singleton. For testing only.

---

### Usage Pattern

```python
from agents._base.client import get_project_client

# Get singleton
client = get_project_client(config.azure_ai_project_endpoint)

# Agent operations
agent = client.agents.create_version(...)

# Conversation operations
with client.get_openai_client() as openai_client:
    conversation = openai_client.conversations.create(items=[...])
    response = openai_client.responses.create(...)
```
