# Research: Migrate to New Foundry SDK

**Feature**: 005-migrate-to-new-foundry
**Date**: 2026-03-22
**Purpose**: Resolve all technical unknowns for migrating from `azure-ai-agents` AgentsClient to `azure-ai-projects` v2 AIProjectClient.

---

## 1. SDK Version Strategy

**Decision**: Upgrade to `azure-ai-projects>=2.0.0` (GA, released 2026-03-06). Remove `azure-ai-agents` as a direct dependency.

**Rationale**: v2.0.0 is the first GA release using the v1 Foundry REST APIs. Agent operations are now built into `azure-ai-projects` via the `.agents` sub-client and OpenAI client, eliminating the need for the separate `azure-ai-agents` package. The `from_connection_string()` factory was removed in v1.0.0b11 (2025-05-15), so the current codebase's use of connection strings must be replaced with endpoint URLs.

**Alternatives Considered**:
- Stay on `azure-ai-agents` v1.x: Rejected — package is legacy, no longer receives agent API updates, and does not support the new Conversations/Responses protocol.
- Pin to `azure-ai-projects` v1.x with `azure-ai-agents`: Rejected — v1.x is pre-GA with known breaking changes in every beta; v2.0.0 is the first stable release.

---

## 2. Client Initialization Pattern

**Decision**: Use `AIProjectClient(endpoint=..., credential=...)` constructor directly. The singleton pattern remains — store a single `AIProjectClient` instance, expose both `.agents` sub-client and `.get_openai_client()` as needed.

**Rationale**: The `from_connection_string()` method was removed in v1.0.0b11. The GA constructor takes `endpoint` (a project endpoint URL of form `https://<ai-services>.services.ai.azure.com/api/projects/<project-name>`) and a `TokenCredential`.

**Key Pattern**:
```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

project_client = AIProjectClient(
    endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential()
)
# For agent management:
agent = project_client.agents.create_version(...)
# For conversations/responses:
openai_client = project_client.get_openai_client()
```

**Impact on Singleton**:
- `client.py` stores `AIProjectClient` (replacing `AgentsClient`)
- Need to expose both the project client and convenience methods for getting the OpenAI client
- The `get_agents_client()` function name should change or be supplemented

---

## 3. Agent Lifecycle — create_version vs create_agent

**Decision**: Use `project_client.agents.create_version(agent_name=..., definition=PromptAgentDefinition(...))` for both create and update operations.

**Rationale**: The old `create_agent()` and `update_agent()` methods were removed in v2.0.0b4. The `create_version()` method creates a new version of an agent (or creates the agent if it doesn't exist). The `PromptAgentDefinition` class wraps model, instructions, and tools.

**Key Pattern**:
```python
from azure.ai.projects.models import PromptAgentDefinition

agent = project_client.agents.create_version(
    agent_name="code-helper",
    definition=PromptAgentDefinition(
        model="gpt-4o",
        instructions="...",
        tools=[tool1, tool2],  # Tool objects directly, not flattened definitions
    ),
)
# Agent has: agent.id, agent.name, agent.version
```

**Idempotent Pattern Change**:
- Old: List agents → find by name → create or update
- New: `create_version()` is inherently idempotent — creates a new version each time. No need to check existence first. This simplifies the factory significantly.

**Agent Deletion**:
```python
project_client.agents.delete_version(
    agent_name=agent.name,
    agent_version=agent.version
)
```

---

## 4. Conversation Lifecycle — Replacing Threads/Runs

**Decision**: Use OpenAI client's `conversations` and `responses` APIs instead of the old threads/messages/runs model.

**Rationale**: The v2 SDK aligns with OpenAI's Responses protocol. Threads are replaced by Conversations, Messages by Conversation Items, and Runs by Responses. The OpenAI client (obtained via `project_client.get_openai_client()`) handles all interaction.

**Key Pattern**:
```python
openai_client = project_client.get_openai_client()

# Create conversation with initial message
conversation = openai_client.conversations.create(
    items=[{"type": "message", "role": "user", "content": "Hello!"}],
)

# Get agent response
response = openai_client.responses.create(
    conversation=conversation.id,
    extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
)
print(response.output_text)

# Add follow-up message
openai_client.conversations.items.create(
    conversation_id=conversation.id,
    items=[{"type": "message", "role": "user", "content": "Follow-up question"}],
)

# Get another response
response = openai_client.responses.create(
    conversation=conversation.id,
    extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
)

# Cleanup
openai_client.conversations.delete(conversation_id=conversation.id)
```

**Impact on `run.py`**:
- `run_agent()` needs full rewrite
- No more `client.threads.create()`, `client.messages.create()`, `client.runs.create_and_process()`
- No more `RunStatus`, `MessageRole` enums from `azure.ai.agents.models`
- Response extraction is simpler: `response.output_text`
- Auto function call mechanism changes (now handled via response output items)

---

## 5. Tool Definition Changes

**Decision**: Adapt `FunctionTool` creation to use the new JSON schema constructor. Custom tools still use Python functions, but the wrapping mechanism changes.

**Rationale**: In v2, `FunctionTool` is declared with explicit JSON schema:
```python
from azure.ai.projects.models import FunctionTool

tool = FunctionTool(
    name="greet_user",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "The name"}
        },
        "required": ["name"],
        "additionalProperties": False,
    },
    description="Greet a user by name.",
    strict=True,
)
```

The old pattern `FunctionTool(functions=[python_callable])` no longer works.

**Impact**:
- `create_function_tool()` helper in `agents/_base/tools/__init__.py` must be rewritten
- Each agent's tool modules need updated tool definitions
- Function call handling in responses differs: process `function_call` output items, execute function, return `FunctionCallOutput`

**Tool Execution Pattern (New)**:
```python
# After responses.create(), check for function_call items:
for output in response.output:
    if output.type == "function_call":
        # Execute the function
        result = my_function(**json.loads(output.arguments))
        # Submit result
        response = openai_client.responses.create(
            conversation=conversation.id,
            extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
            input=[{
                "type": "function_call_output",
                "call_id": output.call_id,
                "output": json.dumps(result),
            }],
        )
```

---

## 6. Environment Variable Migration

**Decision**: Rename `FOUNDRY_PROJECT_CONNECTION_STRING` → `AZURE_AI_PROJECT_ENDPOINT` throughout the codebase.

**Rationale**: The new SDK expects a project endpoint URL (not a connection string). The naming aligns with the official SDK documentation and samples, which use `AZURE_AI_PROJECT_ENDPOINT`.

**Endpoint Format**: `https://<ai-services-account>.services.ai.azure.com/api/projects/<project-name>`

**Files Affected**:
- `.env.example`
- `agents/_base/config.py` (field name: `azure_ai_project_endpoint`)
- `agents/code_helper/config.py`
- `agents/doc_assistant/config.py`
- All test fixtures
- All notebooks
- All documentation

---

## 7. Code Interpreter Tool Migration

**Decision**: Use `CodeInterpreterTool` from `azure.ai.projects.models` instead of `azure.ai.agents.models`.

**Rationale**: The import path changes but the usage pattern is similar. The class was renamed from `CodeInterpreterTool` (same name, different package).

```python
from azure.ai.projects.models import CodeInterpreterTool
tool = CodeInterpreterTool()
```

---

## 8. Test Migration Strategy

**Decision**: Update all mocks to target the new SDK classes. Preserve the existing test structure, markers, and isolation strategy.

**Rationale**: The test pyramid doesn't change — only the mocked API surface changes. Key changes:
- Mock `AIProjectClient` instead of `AgentsClient`
- Mock `.agents.create_version()` instead of `.create_agent()` / `.update_agent()`
- Mock OpenAI client's `.conversations` and `.responses` instead of `.threads`, `.messages`, `.runs`
- `AgentRunError` custom exception still makes sense for run failures

**Unit Test Mock Pattern**:
```python
@pytest.fixture
def mock_project_client():
    client = MagicMock(spec=AIProjectClient)
    client.agents = MagicMock()
    openai_client = MagicMock()
    client.get_openai_client.return_value.__enter__ = MagicMock(return_value=openai_client)
    client.get_openai_client.return_value.__exit__ = MagicMock(return_value=False)
    return client, openai_client
```

---

## 9. Notebook Migration Strategy

**Decision**: Update all 3 notebooks in-place. Use context managers as recommended by the SDK docs.

**Rationale**: The SDK docs recommend using context managers (`with` statements) for both `DefaultAzureCredential` and `AIProjectClient`. This ensures proper resource cleanup.

**Notebook 01 (Setup)**:
```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
project_client = AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential()
)
```

**Notebook 02 (Build & Run)** — the current selection:
- Agent creation via `project_client.agents.create_version()`
- Conversation via `openai_client.conversations.create()`
- Response via `openai_client.responses.create()`
- Cleanup via `openai_client.conversations.delete()`

---

## 10. Scaffolding Script Impact

**Decision**: Update `create_agent.py` templates to generate code using the new SDK patterns.

**Rationale**: The scaffolding script generates boilerplate for new agents. Generated code must use `create_version`, `PromptAgentDefinition`, and the new `FunctionTool` schema format. Integration test templates must use conversations/responses.

**Key Template Changes**:
- Config class: `azure_ai_project_endpoint` field
- Tool template: JSON schema `FunctionTool` declaration
- Integration test: conversations/responses instead of threads/runs
