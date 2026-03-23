# Contract: Agent Run Lifecycle

**Feature**: 005-migrate-to-new-foundry
**Module**: `agents/_base/run.py`

## Public API

### `run_agent(endpoint: str, agent_name: str, prompt: str) -> str`

Runs a single-turn conversation with a deployed agent and returns the response text.

**Parameters**:
- `endpoint` (str): Azure AI Project endpoint URL
- `agent_name` (str): The agent name (used in agent_reference)
- `prompt` (str): User message to send

**Returns**: `str` — agent's response text

**Behaviour**:
1. Get `AIProjectClient` singleton via `get_project_client(endpoint)`
2. Get OpenAI client via `project_client.get_openai_client()`
3. Create conversation: `openai_client.conversations.create(items=[{"type": "message", "role": "user", "content": prompt}])`
4. Create response: `openai_client.responses.create(conversation=conversation.id, extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}})`
5. Handle function calls if present (loop until no more function_call items)
6. Extract response: `response.output_text`
7. Delete conversation: `openai_client.conversations.delete(conversation_id=conversation.id)`
8. Return response text

**Error Cases**:
- `AgentRunError` if response status indicates failure
- Conversation always cleaned up (even on error)

---

### Function Call Handling

When `response.output` contains `function_call` items:
1. Look up the function by name in registered tools
2. Execute function with parsed arguments
3. Submit `function_call_output` with result
4. Get next response
5. Repeat until no more function_call items

---

### Response Format

```python
# Success
"Agent's text response here"

# Failure
raise AgentRunError("Run failed: <status> — <details>")
```
