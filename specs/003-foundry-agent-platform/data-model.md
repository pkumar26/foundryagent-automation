# Data Model: Foundry Agent Platform

**Feature**: 003-foundry-agent-platform  
**Date**: 2026-03-18  

---

## Entities

### 1. FoundryBaseConfig

**Purpose**: Shared configuration base for all agents. Reads from environment variables and `.env` files via pydantic-settings.

| Field | Type | Source | Default | Validation |
|-------|------|--------|---------|------------|
| `foundry_project_connection_string` | `str` | Env: `FOUNDRY_PROJECT_CONNECTION_STRING` | (required) | Non-empty string |
| `environment` | `str` | Env: `ENVIRONMENT` | `"dev"` | One of: dev, qa, prod |
| `azure_key_vault_name` | `str` | Env: `AZURE_KEY_VAULT_NAME` | `""` | Optional |

**Relationships**: Extended by every agent-specific config class.

---

### 2. AgentConfig (per agent — pattern, not a literal class)

**Purpose**: Agent-specific configuration pattern. Each agent defines its own subclass of `FoundryBaseConfig` (e.g., `MyAgentConfig(FoundryBaseConfig)`) with its own defaults and additional fields. "AgentConfig" here refers to this pattern, not a single concrete class.

| Field | Type | Source | Default | Validation |
|-------|------|--------|---------|------------|
| `agent_name` | `str` | Env: `AGENT_NAME` | (per agent) | Non-empty, unique across registry |
| `agent_model` | `str` | Env: `AGENT_MODEL` | `"gpt-4o"` | Non-empty |
| `agent_instructions_path` | `str` | Env: `AGENT_INSTRUCTIONS_PATH` | (per agent) | File must exist |
| `knowledge_source_enabled` | `bool` | Env: `KNOWLEDGE_SOURCE_ENABLED` | `False` | — |
| `github_openapi_enabled` | `bool` | Env: `GITHUB_OPENAPI_ENABLED` | `False` | — |
| `azure_ai_search_endpoint` | `str` | Env: `AZURE_AI_SEARCH_ENDPOINT` | `""` | Required if knowledge_source_enabled |
| `azure_ai_search_index_name` | `str` | Env: `AZURE_AI_SEARCH_INDEX_NAME` | `""` | Required if knowledge_source_enabled |
| `github_openapi_endpoint` | `str` | Env: `GITHUB_OPENAPI_ENDPOINT` | `""` | Required if github_openapi_enabled |
| `github_openapi_token_secret_name` | `str` | Env: `GITHUB_OPENAPI_TOKEN_SECRET_NAME` | `""` | Required if github_openapi_enabled |

**Relationships**: Inherits from `FoundryBaseConfig`. Referenced by `AgentRegistryEntry`. Consumed by `agent_factory.create_or_update_agent()`.

---

### 3. AgentRegistryEntry

**Purpose**: An entry in the agent registry mapping an agent name to its config class and factory function.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Unique agent identifier |
| `config_class` | `type[FoundryBaseConfig]` | The pydantic-settings subclass for this agent |
| `factory` | `Callable` | Reference to `create_or_update_agent` (or a custom factory if overridden) |

**Relationships**: Aggregated by the `AgentRegistry`.

**Invariants**:
- `name` must be unique across all entries — enforced at registry load time.
- `config_class` must be a subclass of `FoundryBaseConfig`.

---

### 4. AgentRegistry

**Purpose**: Central registry of all agents. Singleton, loaded at import time from `agents/registry.py`.

| Operation | Signature | Behaviour |
|-----------|-----------|-----------|
| `list_agents()` | `-> list[AgentRegistryEntry]` | Returns all registered entries |
| `get_agent(name)` | `-> AgentRegistryEntry` | Returns entry or raises `KeyError` with descriptive message |
| `validate()` | `-> None` | Checks name uniqueness; raises on duplicates |

**State transitions**: None — registry is immutable after load.

---

### 5. Agent (Azure-side, SDK-managed)

**Purpose**: Represents a deployed agent in Azure AI Foundry. Created/updated via the SDK, not stored locally.

| Attribute | Type | Source | Notes |
|-----------|------|--------|-------|
| `id` | `str` | Azure SDK | Server-assigned, used for update/run |
| `name` | `str` | From config | Matches `agent_name` |
| `model` | `str` | From config | The LLM model identifier |
| `instructions` | `str` | From instructions.md | Loaded at deploy time |
| `tools` | `list` | From tools/ + integration stubs | FunctionTool definitions |

**State transitions**:
- Not exists → Created (via `agents_client.create_agent()`)
- Exists → Updated (via `agents_client.update_agent()`)
- Exists → Deleted (via `agents_client.delete_agent()`, test cleanup only)

---

### 6. Thread (Azure-side, SDK-managed)

**Purpose**: A conversation context for agent interactions.

| Attribute | Type | Source |
|-----------|------|--------|
| `id` | `str` | Azure SDK |

**State transitions**:
- Created (via `agents_client.threads.create()`)
- Deleted (via `agents_client.threads.delete()`, cleanup)

**Relationships**: Contains Messages. Associated with Runs.

---

### 7. Run (Azure-side, SDK-managed)

**Purpose**: An execution instance — the agent processing a thread's messages.

| Attribute | Type | Source |
|-----------|------|--------|
| `id` | `str` | Azure SDK |
| `status` | `RunStatus` | Azure SDK |
| `agent_id` | `str` | From agent |
| `thread_id` | `str` | From thread |

**Terminal statuses**: `completed`, `failed`, `cancelled`  
**Non-terminal statuses**: `queued`, `in_progress`, `requires_action`

**State transitions**:
```
queued → in_progress → completed
                     → failed
                     → cancelled
         in_progress → requires_action → in_progress (after tool call)
```

---

### 8. FunctionTool

**Purpose**: A callable function registered with an agent.

| Attribute | Type | Source |
|-----------|------|--------|
| `functions` | `list[Callable]` | Python functions from `tools/` |
| `definitions` | `list[dict]` | Auto-generated from function signatures |

**Relationships**: Defined in `agents/<name>/tools/`. Passed to agent creation via `tools` parameter.

---

### 9. IntegrationStub

**Purpose**: Placeholder for deferred integrations. Returns `None` when disabled.

| Stub | File | Feature Flag | Returns When Enabled |
|------|------|-------------|---------------------|
| Knowledge Source | `integrations/knowledge.py` | `KNOWLEDGE_SOURCE_ENABLED` | Tool definition (future) |
| GitHub OpenAPI | `integrations/github_openapi.py` | `GITHUB_OPENAPI_ENABLED` | Tool definition (future) |

**Contract**: `get_knowledge_tool(config) -> Optional[ToolDefinition]` and `get_github_openapi_tool(config) -> Optional[ToolDefinition]`

---

## Entity Relationship Summary

```
AgentRegistry 1──* AgentRegistryEntry
AgentRegistryEntry 1──1 AgentConfig (subclass of FoundryBaseConfig)
AgentRegistryEntry 1──1 factory function
AgentConfig ──uses──> AIProjectClient (singleton)
AgentConfig ──creates──> Agent (Azure-side)
Agent 1──* FunctionTool
Agent 1──* IntegrationStub (conditional tools)
Agent 1──* Thread (via runs)
Thread 1──* Message
Thread 1──* Run
```
