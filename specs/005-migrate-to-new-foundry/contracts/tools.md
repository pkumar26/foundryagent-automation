# Contract: Tool Definitions

**Feature**: 005-migrate-to-new-foundry
**Module**: `agents/_base/tools/__init__.py`

## Public API

### `create_function_tool(func: Callable, description: str | None = None) -> FunctionTool`

Creates a `FunctionTool` from a Python function by inspecting its signature and generating a JSON schema.

**Parameters**:
- `func` (Callable): Python function to wrap as a tool
- `description` (str | None): Optional description override (defaults to function docstring)

**Returns**: `FunctionTool` — tool object ready for use in `PromptAgentDefinition`

**Behaviour**:
1. Extract function name
2. Extract description from docstring or parameter
3. Inspect function signature to build JSON schema for parameters
4. Return `FunctionTool(name=..., parameters=schema, description=..., strict=True)`

---

### Per-Agent Tool Modules

Each agent exposes a `TOOLS` list in `agents/<agent>/tools/__init__.py`:

```python
# agents/code_helper/tools/__init__.py
from agents._base.tools import create_function_tool
from agents.code_helper.tools.sample_tool import greet_user

TOOLS = [create_function_tool(greet_user)]
```

### Tool Schema Format (New)

```python
FunctionTool(
    name="greet_user",
    parameters={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The name of the user to greet"
            }
        },
        "required": ["name"],
        "additionalProperties": False,
    },
    description="Greet a user by name and return a greeting message.",
    strict=True,
)
```

### Supported Parameter Types

| Python Type | JSON Schema Type |
|-------------|------------------|
| `str` | `"string"` |
| `int` | `"integer"` |
| `float` | `"number"` |
| `bool` | `"boolean"` |
| `list` | `"array"` |
| `dict` | `"object"` |
