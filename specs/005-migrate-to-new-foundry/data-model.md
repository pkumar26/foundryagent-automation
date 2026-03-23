# Data Model: Migrate to New Foundry SDK

**Feature**: 005-migrate-to-new-foundry
**Date**: 2026-03-22
**Purpose**: Document entity changes, configuration field renames, and relationship updates for the SDK migration.

---

## 1. Configuration Entities

### 1.1 FoundryBaseConfig (CHANGED)

**Location**: `agents/_base/config.py`

| Field | Old Name | New Name | Type | Required | Default | Notes |
|-------|----------|----------|------|----------|---------|-------|
| Endpoint | `foundry_project_connection_string` | `azure_ai_project_endpoint` | `str` | Yes | — | URL format: `https://<account>.services.ai.azure.com/api/projects/<project>` |
| Environment | `environment` | `environment` | `Literal["dev","qa","prod"]` | No | `"dev"` | Unchanged |
| Key Vault | `azure_key_vault_name` | `azure_key_vault_name` | `str` | No | `""` | Unchanged |

**Validation**: `azure_ai_project_endpoint` must be a valid HTTPS URL starting with `https://`.

### 1.2 Agent-Specific Configs (CHANGED)

**CodeHelperConfig** (`agents/code_helper/config.py`):

| Field | Change | Notes |
|-------|--------|-------|
| `foundry_project_connection_string` | Inherited from base → now `azure_ai_project_endpoint` | |
| `agent_name` | Unchanged: `"code-helper"` | |
| `agent_model` | Unchanged: `"gpt-4o"` | |
| `agent_instructions_path` | Unchanged | |
| `knowledge_source_enabled` | Unchanged: `False` | |
| `azure_ai_search_connection_id` | Unchanged: `""` | |
| `azure_ai_search_index_name` | Unchanged: `""` | |
| `code_interpreter_enabled` | Unchanged: `False` | |

**DocAssistantConfig** (`agents/doc_assistant/config.py`): Same changes as CodeHelperConfig (inherits from base).

---

## 2. Client Entities

### 2.1 Client Singleton (CHANGED)

**Location**: `agents/_base/client.py`

| Aspect | Old | New |
|--------|-----|-----|
| Class | `AgentsClient` | `AIProjectClient` |
| Import | `from azure.ai.agents import AgentsClient` | `from azure.ai.projects import AIProjectClient` |
| Constructor | `AgentsClient(endpoint=conn_str, credential=cred)` | `AIProjectClient(endpoint=endpoint_url, credential=cred)` |
| Singleton variable | `_client: Optional[AgentsClient]` | `_client: Optional[AIProjectClient]` |
| Agent ops | `_client.create_agent()`, `_client.list_agents()` | `_client.agents.create_version()` |
| Conversation ops | `_client.threads`, `_client.messages`, `_client.runs` | Via `_client.get_openai_client()` |

### 2.2 OpenAI Client (NEW)

The v2 SDK introduces an OpenAI client obtained via `project_client.get_openai_client()`. This is a context manager that returns an authenticated `AzureOpenAI` client. The run lifecycle (conversations, responses) uses this client.

| Operation | Old API | New API |
|-----------|---------|---------|
| Create thread/conversation | `client.threads.create()` | `openai_client.conversations.create(items=[...])` |
| Post message | `client.messages.create(thread_id, role, content)` | `openai_client.conversations.items.create(conversation_id, items=[...])` |
| Execute run | `client.runs.create_and_process(thread_id, agent_id)` | `openai_client.responses.create(conversation=id, extra_body={"agent_reference": {...}})` |
| Get response text | `client.messages.get_last_message_text_by_role(thread_id, role)` | `response.output_text` |
| Delete thread/conversation | `client.threads.delete(thread_id)` | `openai_client.conversations.delete(conversation_id=id)` |
| Auto function calls | `client.enable_auto_function_calls(tool)` | Manual: loop on `function_call` output items, submit `function_call_output` |

---

## 3. Agent Entities

### 3.1 Agent Object (CHANGED)

| Property | Old (`azure.ai.agents` Agent) | New (create_version result) |
|----------|-------------------------------|------------------------------|
| `id` | `agent.id` | `agent.id` |
| `name` | `agent.name` | `agent.name` |
| `model` | `agent.model` | Via definition |
| `version` | N/A | `agent.version` (NEW — version string) |

### 3.2 Agent Definition (NEW)

```python
from azure.ai.projects.models import PromptAgentDefinition

definition = PromptAgentDefinition(
    model="gpt-4o",
    instructions="...",
    tools=[tool1, tool2],
)
```

---

## 4. Tool Entities

### 4.1 FunctionTool (CHANGED)

| Aspect | Old | New |
|--------|-----|-----|
| Import | `from azure.ai.agents.models import FunctionTool` | `from azure.ai.projects.models import FunctionTool` |
| Constructor | `FunctionTool(functions=[callable])` | `FunctionTool(name=str, parameters=dict, description=str, strict=bool)` |
| Schema | Auto-generated from function signature + docstring | Explicit JSON Schema dictionary |
| Passing to agent | `tool.definitions` (list of defs) | Tool object directly in `tools=[]` list |

### 4.2 CodeInterpreterTool (CHANGED)

| Aspect | Old | New |
|--------|-----|-----|
| Import | `from azure.ai.agents.models import CodeInterpreterTool` | `from azure.ai.projects.models import CodeInterpreterTool` |
| Usage | Same: `CodeInterpreterTool()` | Same: `CodeInterpreterTool()` |

---

## 5. Run/Response Entities

### 5.1 Response Object (REPLACES Run)

| Old Entity | New Entity | Notes |
|------------|------------|-------|
| `Run` | Response from `responses.create()` | |
| `RunStatus.COMPLETED` | Check `response.status` | |
| `RunStatus.FAILED` | Check `response.status` | |
| `MessageRole.AGENT` | N/A — use `response.output_text` directly | |
| `ThreadMessage` | Conversation items | |

---

## 6. Entity Relationship Diagram

```
┌──────────────────────┐
│   FoundryBaseConfig   │
│ azure_ai_project_     │──── env: AZURE_AI_PROJECT_ENDPOINT
│    endpoint           │
│ environment           │
└──────────┬───────────┘
           │ inherits
    ┌──────┴──────┐
    │             │
┌───┴───┐   ┌────┴────┐
│CodeHelp│   │DocAssist│
│Config  │   │ Config  │
└───┬────┘   └────┬────┘
    │             │
    └──────┬──────┘
           │ uses
    ┌──────┴──────┐
    │AIProjectClient│── singleton
    │  (client.py)  │
    └──────┬──────┘
           │ exposes
    ┌──────┴──────┐
    │  .agents     │── create_version(), delete_version()
    │  sub-client  │
    └──────────────┘
           │
    ┌──────┴──────────┐
    │.get_openai_client│── conversations, responses
    │  (OpenAI client) │
    └─────────────────┘
```

---

## 7. Environment Variable Mapping

| Old | New | Format |
|-----|-----|--------|
| `FOUNDRY_PROJECT_CONNECTION_STRING` | `AZURE_AI_PROJECT_ENDPOINT` | `https://<account>.services.ai.azure.com/api/projects/<project>` |

No other environment variables change.
