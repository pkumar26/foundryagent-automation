# Feature Specification: Migrate to New Foundry SDK (azure-ai-projects v2)

**Feature Branch**: `005-migrate-to-new-foundry`
**Created**: 2026-03-22
**Status**: Approved
**Input**: User description: "Move away from old Foundry to new Foundry — migrate from azure-ai-agents AgentsClient to azure-ai-projects v2 AIProjectClient with the new Conversations/Responses-based agent interaction model."

## Summary

Migrate the entire foundryagent-automation codebase from the legacy agent SDK (`azure-ai-agents` with `AgentsClient`, threads, and runs) to the current GA `azure-ai-projects` v2.x SDK (`AIProjectClient`, `create_version`, OpenAI-based conversations/responses). This is a breaking infrastructure change that touches the client singleton, agent factory, run lifecycle, tool definitions, configuration, tests, notebooks, scripts, and documentation.

## Functional Requirements

### FR-001: Client Migration
Replace `AgentsClient` singleton with `AIProjectClient` singleton. The new client uses `endpoint=` (project endpoint URL), not a connection string. The `.agents` sub-client provides agent management operations. An OpenAI client via `.get_openai_client()` provides conversation and response operations.

### FR-002: Agent Lifecycle Migration
Replace `create_agent()` / `update_agent()` with `create_version()` using `PromptAgentDefinition`. The idempotent create-or-update pattern must be preserved via `create_version()`'s inherent idempotency — calling it with the same agent name creates a new version without needing to list or match existing agents.

### FR-003: Conversation Lifecycle Migration
Replace threads/messages/runs with OpenAI conversations/responses. The OpenAI client is obtained via `project_client.get_openai_client()`, which returns a context manager — all conversation operations MUST occur within a `with` block:
- `client.threads.create()` → `openai_client.conversations.create(items=[...])`
- `client.messages.create()` → `openai_client.conversations.items.create()`
- `client.runs.create_and_process()` → `openai_client.responses.create(conversation=..., extra_body={"agent_reference": {...}})`
- Response text extraction from `response.output_text`
- Conversation cleanup via `openai_client.conversations.delete(conversation_id=...)` in a `finally` block

Function call handling is manual: after each `responses.create()`, the caller MUST iterate over `response.output` items, execute any with `type == "function_call"` by looking up the named function, and submit results via a follow-up `responses.create()` with a `function_call_output` item. This loop repeats until the response contains no more `function_call` items.

### FR-004: Tool Definition Migration
`FunctionTool` constructor changed from `FunctionTool(functions=[python_callable])` to JSON schema-based: `FunctionTool(name=..., parameters={...}, description=...)`. The `create_function_tool` helper signature changes from `create_function_tool(functions: list) -> FunctionTool` to `create_function_tool(func: Callable, description: str | None = None) -> FunctionTool` (single function, not a list). All call sites change from `create_function_tool([fn])` to `create_function_tool(fn)`.

### FR-005: Environment Variable Migration
Replace `FOUNDRY_PROJECT_CONNECTION_STRING` with `AZURE_AI_PROJECT_ENDPOINT`. Update `.env.example`, all config classes, documentation, and notebooks.

### FR-006: Dependency Update
Update `pyproject.toml` and `requirements.txt`:
- `azure-ai-projects>=2.0.0` (was `>=1.0.0b1`)
- Remove `azure-ai-agents` as a direct dependency (agent operations now built into azure-ai-projects v2)
- Keep `azure-identity>=1.15.0` and `pydantic-settings>=2.0.0`

### FR-007: Test Migration
Update all unit and integration tests to mock/use the new SDK classes. Preserve the existing test structure and marker strategy (unit vs integration, per-agent markers).

### FR-008: Notebook Migration
Update all 3 notebooks to use the new SDK patterns. Notebooks must remain runnable end-to-end with the new API.

### FR-009: Script Migration
Update `create_agent.py` (scaffolding templates) to generate code using the new SDK patterns. `deploy_agent.py` requires no changes — it delegates entirely to the agent factory, which handles the SDK migration internally.

### FR-010: Documentation Update
Update README.md, custom-tools-guide.md, and all docs to reflect the new SDK patterns.

## Non-Functional Requirements

### NFR-001: Backward Compatibility
This is an intentional breaking change. No backward compatibility with the old `AgentsClient` API is required.

### NFR-002: No Feature Regression
All existing agent capabilities (create, update, deploy, run, tools, knowledge stub) must continue to work under the new SDK.

### NFR-003: Idempotency
The create-or-update agent pattern must remain idempotent.

## User Scenarios

### US-1: Developer deploys agent with new SDK (P1)
**Given** a developer has set `AZURE_AI_PROJECT_ENDPOINT`, **When** they run `deploy_agent.py --name code-helper`, **Then** the agent is created/updated in Foundry using the new `create_version` API.

### US-2: Developer runs agent conversation (P1)
**Given** a deployed agent, **When** the developer uses the notebook to send a message, **Then** the conversation is created via `openai_client.conversations`, the response is generated via `openai_client.responses.create()`, and the output text is returned.

### US-3: Developer scaffolds new agent (P2)
**Given** a developer runs `create_agent.py --name my-agent`, **Then** generated code uses the new SDK patterns (AIProjectClient, create_version, conversations).

### US-4: Unit tests pass without Azure credentials (P1)
**Given** no Azure credentials, **When** `pytest` runs unit tests, **Then** all unit tests pass with mocked new SDK classes.

## Out of Scope
- Knowledge source integration (remains a stub)
- GitHub OpenAPI integration (remains a stub)
- Infrastructure changes (Terraform/Bicep — already correct)
- Adding new agent capabilities beyond what exists today
