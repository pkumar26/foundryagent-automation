# Custom Tools Guide

[![Azure AI Foundry](https://img.shields.io/badge/Azure%20AI-Foundry-0078D4?logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/en-us/products/ai-services)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)

This guide walks you through adding custom tools to any agent in the platform — from writing your first tool function to testing and deploying it.

## How Tools Work

Tools let your agent call Python functions during a conversation. When the agent decides it needs a tool, the SDK:

1. Pauses the agent's response
2. Calls your Python function with the arguments the agent chose
3. Sends the function's return value back to the agent
4. The agent incorporates the result into its response

The platform uses Azure AI Foundry's `FunctionTool`, which automatically generates a JSON schema from your function's signature and docstring — no manual schema writing needed.

## Quick Start: Add a Tool in 3 Steps

### 1. Write the Function

Create a new file in your agent's `tools/` directory:

```python
# agents/code_helper/tools/calculator.py
from agents._base.tools import create_function_tool


def add_numbers(a: int, b: int) -> str:
    """Add two numbers together.

    Args:
        a: The first number.
        b: The second number.

    Returns:
        The sum as a string.
    """
    return str(a + b)


# Export the tool — the factory picks this up automatically
TOOLS = [create_function_tool([add_numbers])]
```

### 2. Register in `__init__.py`

Update the agent's tools `__init__.py` to include your new tool:

```python
# agents/code_helper/tools/__init__.py
"""Code-helper agent tools."""

from agents.code_helper.tools.sample_tool import TOOLS as SAMPLE_TOOLS
from agents.code_helper.tools.calculator import TOOLS as CALC_TOOLS

TOOLS = SAMPLE_TOOLS + CALC_TOOLS

__all__ = ["TOOLS"]
```

### 3. Redeploy

```bash
uv run python scripts/deploy_agent.py --agent code-helper
```

The factory detects the updated `TOOLS` list and pushes the new tool definitions to Azure.

## Function Requirements

Tool functions must follow these rules for the SDK to generate correct schemas:

| Requirement | Why |
|-------------|-----|
| **Type hints on all parameters** | SDK uses them to build the JSON schema |
| **Docstring with `Args:` section** | SDK uses parameter descriptions in the schema |
| **Return a string** | The return value is sent back to the agent as text |
| **No `*args` or `**kwargs`** | SDK cannot generate schemas for variadic params |

### Good Example

```python
def search_docs(query: str, max_results: int = 5) -> str:
    """Search the documentation for relevant articles.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return.

    Returns:
        Matching article titles and snippets, one per line.
    """
    # Your implementation
    results = do_search(query, max_results)
    return "\n".join(f"- {r.title}: {r.snippet}" for r in results)
```

### What to Avoid

```python
# BAD: No type hints — SDK can't build schema
def search_docs(query, max_results=5):
    ...

# BAD: Returns dict — agent receives repr() which is messy
def search_docs(query: str) -> dict:
    return {"results": [...]}

# BAD: No docstring — SDK uses "No description" for every param
def search_docs(query: str) -> str:
    return do_search(query)
```

## Grouping Multiple Functions

You can group related functions into a single `FunctionTool`. Functions in the same tool share a registration unit — group them when they're logically related:

```python
# agents/code_helper/tools/math_tools.py
from agents._base.tools import create_function_tool


def add(a: int, b: int) -> str:
    """Add two numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        The sum.
    """
    return str(a + b)


def multiply(a: int, b: int) -> str:
    """Multiply two numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        The product.
    """
    return str(a * b)


# Both functions registered as one tool
TOOLS = [create_function_tool([add, multiply])]
```

Or keep them as separate tools if they serve different purposes:

```python
TOOLS = [
    create_function_tool([add, subtract]),      # arithmetic tool
    create_function_tool([search_docs]),         # search tool
]
```

## Handling Errors

If your tool function raises an exception, the SDK sends the error message back to the agent, which may retry or respond with an error explanation. For predictable behaviour, catch exceptions and return error strings:

```python
import json

def fetch_weather(city: str) -> str:
    """Get current weather for a city.

    Args:
        city: City name (e.g., "Seattle").

    Returns:
        Weather summary or error message.
    """
    try:
        data = weather_api.get(city)
        return f"Weather in {city}: {data['temp']}°F, {data['condition']}"
    except Exception as e:
        return f"Could not fetch weather for {city}: {e}"
```

## Optional Parameters

Use default values for optional parameters. The SDK marks parameters without defaults as `required` in the schema:

```python
def search(query: str, language: str = "en", max_results: int = 10) -> str:
    """Search with optional filters.

    Args:
        query: Search query (required).
        language: Language code to filter by.
        max_results: Maximum results to return.

    Returns:
        Search results.
    """
    ...
```

The agent sees `query` as required and `language`/`max_results` as optional.

## Testing Your Tools

### Unit Tests

Write unit tests alongside your tools. The existing pattern in the repo:

```python
# tests/code_helper/test_calculator.py
import pytest
from agents.code_helper.tools.calculator import add_numbers

pytestmark = pytest.mark.code_helper


class TestAddNumbers:
    def test_adds_positive_numbers(self):
        assert add_numbers(2, 3) == "5"

    def test_adds_negative_numbers(self):
        assert add_numbers(-1, -2) == "-3"

    def test_returns_string(self):
        assert isinstance(add_numbers(1, 1), str)
```

Run with:

```bash
uv run pytest tests/code_helper/test_calculator.py -v
```

### Interactive Testing

After deploying, test the tool end-to-end in the notebook `02_build_and_run_agent.ipynb`. Change the message in Step 2 to trigger your tool:

```python
content = "What is 42 + 58?"  # triggers add_numbers tool
```

## Complete Walkthrough: Adding a File Reader Tool

Here's a full example — adding a tool that reads a file and returns its contents:

**1. Create the tool file:**

```python
# agents/code_helper/tools/file_reader.py
from pathlib import Path

from agents._base.tools import create_function_tool

ALLOWED_EXTENSIONS = {".py", ".md", ".txt", ".json", ".yaml", ".yml"}


def read_file(filepath: str) -> str:
    """Read the contents of a file.

    Args:
        filepath: Relative path to the file to read.

    Returns:
        The file contents, or an error message.
    """
    path = Path(filepath)

    if not path.exists():
        return f"File not found: {filepath}"

    if path.suffix not in ALLOWED_EXTENSIONS:
        return f"File type not supported: {path.suffix}"

    try:
        content = path.read_text(encoding="utf-8")
        if len(content) > 4000:
            content = content[:4000] + "\n... (truncated)"
        return content
    except Exception as e:
        return f"Error reading file: {e}"


TOOLS = [create_function_tool([read_file])]
```

**2. Update `__init__.py`:**

```python
# agents/code_helper/tools/__init__.py
"""Code-helper agent tools."""

from agents.code_helper.tools.sample_tool import TOOLS as GREETING_TOOLS
from agents.code_helper.tools.file_reader import TOOLS as FILE_TOOLS

TOOLS = GREETING_TOOLS + FILE_TOOLS

__all__ = ["TOOLS"]
```

**3. Add tests:**

```python
# tests/code_helper/test_file_reader.py
import pytest
from agents.code_helper.tools.file_reader import read_file

pytestmark = pytest.mark.code_helper


class TestReadFile:
    def test_reads_existing_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        assert read_file(str(f)) == "hello world"

    def test_returns_error_for_missing_file(self):
        result = read_file("nonexistent.txt")
        assert "not found" in result.lower()

    def test_rejects_unsupported_extension(self, tmp_path):
        f = tmp_path / "binary.exe"
        f.write_bytes(b"\x00")
        result = read_file(str(f))
        assert "not supported" in result.lower()

    def test_truncates_large_files(self, tmp_path):
        f = tmp_path / "large.txt"
        f.write_text("x" * 5000)
        result = read_file(str(f))
        assert "truncated" in result
```

**4. Run tests and deploy:**

```bash
uv run pytest tests/code_helper/test_file_reader.py -v
uv run python scripts/deploy_agent.py --agent code-helper
```

## File Structure Reference

```
agents/code_helper/
├── tools/
│   ├── __init__.py          # Aggregates TOOLS from all tool files
│   ├── sample_tool.py       # greet_user (ships with scaffold)
│   ├── calculator.py        # Your new tool
│   └── file_reader.py       # Another new tool
```

The factory in `agents/_base/agent_factory.py` imports `agents.{agent_name}.tools` and collects the `TOOLS` list automatically — no other wiring needed.

## What About External APIs?

This guide covers **local Python tools** (`FunctionTool`). To connect your agent to external services like GitHub, Azure AI Search, Bing, or any REST API via OpenAPI specs, see the [OpenAPI & External Tools Guide](openapi-integration-guide.md).

## Checklist

- [ ] Function has type hints on all parameters
- [ ] Function has a docstring with `Args:` section
- [ ] Function returns a `str`
- [ ] `TOOLS` list exported at module level
- [ ] `tools/__init__.py` updated to aggregate the new `TOOLS`
- [ ] Unit tests written and passing
- [ ] Agent redeployed with `deploy_agent.py`
- [ ] Tested interactively via notebook or prompt
