# Contract: Agent Factory

**Feature**: 005-migrate-to-new-foundry
**Module**: `agents/_base/agent_factory.py`

## Public API

### `create_or_update_agent(config: FoundryBaseConfig) -> AgentVersionDetails`

Creates or updates an agent in Azure AI Foundry using `create_version`. Loads instructions from markdown file, collects tools from agent module, and creates a new version.

**Parameters**:
- `config` (FoundryBaseConfig): Agent configuration with endpoint, model, name, instructions path

**Returns**: Agent version object with `.id`, `.name`, `.version` properties

**Behaviour**:
1. Load instructions from `config.agent_instructions_path`
2. Import tools from `agents.<agent_module>.tools.TOOLS`
3. Conditionally add `CodeInterpreterTool` if `config.code_interpreter_enabled`
4. Call `project_client.agents.create_version(agent_name=..., definition=PromptAgentDefinition(...))`
5. Return the agent version object

**Error Cases**:
- `FileNotFoundError` if instructions file doesn't exist
- `ValueError` if instructions file is empty
- SDK exceptions propagated for API failures

---

### Tool Collection

Tools are collected from:
1. `agents.<agent_module_name>.tools.TOOLS` — list of `FunctionTool` objects
2. `CodeInterpreterTool()` — conditional on `config.code_interpreter_enabled`
3. Knowledge source tool — conditional on `config.knowledge_source_enabled` (stub)

All tools are passed as a flat list in `PromptAgentDefinition(tools=[...])`.

---

### Idempotency

`create_version()` is inherently idempotent — calling it multiple times with the same agent name creates new versions. The agent name is the stable identifier; versions are immutable snapshots.
