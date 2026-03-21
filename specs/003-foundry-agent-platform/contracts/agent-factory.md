# Contract: Agent Factory

**Feature**: 003-foundry-agent-platform  
**Module**: `agents/_base/agent_factory.py`  
**Consumers**: Agent registry entries, deploy script, notebooks

---

## Purpose

Shared function that creates or idempotently updates an agent in Azure AI Foundry. Handles the full agent lifecycle: load instructions, assemble tools (including conditional integration stubs), check for existing agent by name, create or update.

## Interface

```python
from azure.ai.agents.models import Agent
from agents._base.config import FoundryBaseConfig


def create_or_update_agent(config: FoundryBaseConfig) -> Agent:
    """Create a new agent or update an existing one idempotently.

    Steps:
    1. Load instructions from config.agent_instructions_path
    2. Collect tools from the agent's tools/ module
    3. Conditionally append knowledge tool (if KNOWLEDGE_SOURCE_ENABLED)
    4. Conditionally append GitHub OpenAPI tool (if GITHUB_OPENAPI_ENABLED)
    5. List existing agents, find by name
    6. If found: update_agent() with new instructions, model, tools
    7. If not found: create_agent() with all parameters
    8. Return the Agent object

    Args:
        config: An agent-specific config object (subclass of FoundryBaseConfig).

    Returns:
        The created or updated Agent object from the SDK.

    Raises:
        FileNotFoundError: If the instructions file does not exist.
        ValueError: If the instructions file is empty.
        azure.core.exceptions.HttpResponseError: On Azure API failures.
    """
    ...
```

## Behaviour Contract

| Input State | Action | Outcome |
|-------------|--------|---------|
| Agent does not exist by name | `create_agent()` | New agent created, returned |
| Agent exists by name | `update_agent()` | Existing agent updated with new instructions/model/tools, returned |
| Instructions file missing | Raise `FileNotFoundError` | No API call made |
| Instructions file empty | Raise `ValueError` | No API call made |
| `KNOWLEDGE_SOURCE_ENABLED=false` | `get_knowledge_tool()` returns `None` | Knowledge tool not appended |
| `KNOWLEDGE_SOURCE_ENABLED=true` | `get_knowledge_tool()` returns tool def | Knowledge tool appended to tools list |
| `GITHUB_OPENAPI_ENABLED=false` | `get_github_openapi_tool()` returns `None` | OpenAPI tool not appended |
| `GITHUB_OPENAPI_ENABLED=true` | `get_github_openapi_tool()` returns tool def | OpenAPI tool appended to tools list |

## Idempotency Guarantee

Running `create_or_update_agent(config)` N times with the same config produces the same agent state as running it once. The agent's `id` is stable across updates (Azure preserves it).

## Dependencies

- `agents._base.client.get_client()` — singleton AIProjectClient
- `agents.<name>.integrations.knowledge.get_knowledge_tool(config)` — optional tool
- `agents.<name>.integrations.github_openapi.get_github_openapi_tool(config)` — optional tool
- Agent's `tools/` module — FunctionTool definitions
