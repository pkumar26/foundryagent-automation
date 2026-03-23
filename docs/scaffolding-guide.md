# Agent Scaffolding Guide

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg?logo=python&logoColor=white)
![CLI Tool](https://img.shields.io/badge/CLI-create__agent.py-green?logo=gnubash&logoColor=white)
![Azure AI Foundry](https://img.shields.io/badge/Azure-AI%20Foundry-0078D4?logo=microsoftazure&logoColor=white)

## Overview

`scripts/create_agent.py` is a zero-dependency CLI tool that scaffolds a new Azure AI Foundry agent in seconds. It generates the full agent directory, test stubs, and registry entry — matching the exact patterns used by existing agents like `code_helper` and `doc_assistant`. Three creation modes are supported: CLI with `--name`, YAML input with `--from-file`, and GitHub Actions via `create-agent.yml`.

## Prerequisites

- **Python 3.11+** with [uv](https://docs.astral.sh/uv/) installed
- The repository cloned and dependencies installed (`uv sync`)
- No additional packages required — the script uses only the Python standard library

## Quick Start

```bash
# Scaffold a new agent
uv run python scripts/create_agent.py --name my-agent
```

Output:
```
[scaffold] ✓ Agent 'my-agent' scaffolded successfully
[scaffold]   Created: agents/my_agent/
[scaffold]   Created: tests/my_agent/
[scaffold]   Updated: agents/registry.py
[scaffold]   Files generated: 13
[scaffold]
[scaffold]   Next steps:
[scaffold]   1. Edit agents/my_agent/instructions.md with agent instructions
[scaffold]   2. Add custom tools in agents/my_agent/tools/
[scaffold]   3. Run tests: uv run pytest tests/my_agent/ -v
[scaffold]   4. Deploy: uv run python scripts/deploy_agent.py --name my-agent
```

## CLI Reference

```
usage: create_agent.py [-h] (--name NAME | --from-file FROM_FILE) [--model MODEL]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--name` | Yes* | — | Agent name in kebab-case (e.g., `my-agent`) |
| `--from-file` | Yes* | — | Path to YAML config file |
| `--model` | No | `gpt-4o` | Model name for the agent |
| `--help` | No | — | Show help message |

\* `--name` and `--from-file` are mutually exclusive — exactly one is required.

### Name Validation Rules

- Lowercase kebab-case only: `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`
- Maximum 50 characters
- Cannot be a Python reserved word (e.g., `class`, `import`, `return`)
- Must not conflict with an existing agent directory or registry entry

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Validation error (invalid name, agent exists) |
| 2 | Filesystem error (permission denied, write failure) |

## YAML Input Reference

### Schema

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `name` | Yes | — | Agent name in kebab-case |
| `model` | No | `gpt-4o` | Model name |

### Example File

```yaml
# agent-config.yaml
name: my-agent
model: gpt-4o-mini
```

### Usage

```bash
uv run python scripts/create_agent.py --from-file agent-config.yaml
```

When `--from-file` is used, the `model` value from the YAML file takes precedence over any `--model` CLI flag.

## GitHub Actions

The `create-agent.yml` workflow provides a browser-based way to scaffold agents:

1. Go to **Actions** → **Create Agent** in your GitHub repository
2. Click **Run workflow**
3. Enter the agent name (required) and model (optional, defaults to `gpt-4o`)
4. The workflow runs the scaffolding script, creates a branch `scaffold/{agent-name}`, commits, and opens a PR

The PR contains all generated files ready for review and customisation before merging.

## What Gets Generated

```
agents/{module_name}/
├── __init__.py              # Package init
├── config.py                # Agent configuration (extends FoundryBaseConfig)
├── instructions.md          # System instructions (markdown)
├── README.md                # Agent documentation with badges, config, and usage
├── tools/
│   ├── __init__.py          # Exports TOOLS list
│   └── sample_tool.py       # Sample greeting tool
└── integrations/
    ├── __init__.py          # Package init
    └── knowledge.py         # Knowledge source stub (returns None when disabled)

tests/{module_name}/
├── __init__.py              # Package init
├── conftest.py              # Fixtures with MonkeyPatch for env vars
├── test_tools.py            # Unit tests for the sample tool
├── test_agent_create.py     # Integration test stub for agent creation
└── test_agent_run.py        # Integration test stub for run lifecycle

agents/registry.py           # Updated with import + AgentRegistryEntry
```

**Total**: 13 files created + 1 file updated = 14 file operations

## Customise Your Agent

After scaffolding, follow these steps to build your agent:

### 1. Edit Instructions

Open `agents/{module_name}/instructions.md` and replace the placeholder content with your agent's system prompt — its role, capabilities, and behaviour guidelines.

### 2. Add Custom Tools

Edit `agents/{module_name}/tools/sample_tool.py` or create new tool files:

```python
# agents/my_agent/tools/my_tool.py
from agents._base.tools import create_function_tool

def search_docs(query: str) -> str:
    """Search documentation for a query."""
    # Your implementation here
    return f"Results for: {query}"

TOOLS = [create_function_tool(search_docs)]
```

Update `agents/{module_name}/tools/__init__.py` to import your new tools.

See the [Custom Tools Guide](custom-tools-guide.md) for full details on function requirements, testing, error handling, and a complete walkthrough.

### 3. Update Config

Edit `agents/{module_name}/config.py` to add agent-specific settings:

```python
class MyAgentConfig(FoundryBaseConfig):
    agent_name: str = "my-agent"
    agent_model: str = "gpt-4o"
    agent_instructions_path: str = "agents/my_agent/instructions.md"
    # Add custom fields:
    max_results: int = 10
    api_endpoint: str = ""
```

### 4. Enable Integrations

Enable per-agent integrations by setting flags in your config:

```python
# Knowledge source (Azure AI Search)
knowledge_source_enabled: bool = True
azure_ai_search_connection_id: str = "your-connection-id"
azure_ai_search_index_name: str = "your-index-name"

# Code Interpreter (sandboxed Python execution)
code_interpreter_enabled: bool = True

# Web Search (web search grounding)
web_search_enabled: bool = True

# GitHub MCP (attach GitHub MCP server from your Foundry project)
github_enabled: bool = True
github_project_connection_id: str = "your-github-connection-id"
```

For knowledge source, also implement the integration function in `agents/{module_name}/integrations/knowledge.py`. Code Interpreter, Web Search, and GitHub MCP require no additional code — just set the flag (and connection ID for GitHub MCP).

### 5. Write Tests

Update the generated test stubs in `tests/{module_name}/` with real assertions:

```bash
# Run your agent's tests
uv run pytest tests/my_agent/ -v
```

### 6. Deploy

```bash
uv run python scripts/deploy_agent.py --name my-agent
```

## FAQ

**How do I rename an agent after scaffolding?**

There is no automated rename command. You need to: (1) rename the directory under `agents/` and `tests/`, (2) update all class names and imports, (3) update the `agent_name` in config, (4) update the registry entry. It's simpler to scaffold a new agent with the correct name and migrate your custom code.

**How do I delete a scaffolded agent?**

Use the deletion script:

```bash
# With confirmation prompt
uv run python scripts/delete_agent.py --name my-agent

# Skip confirmation
uv run python scripts/delete_agent.py --name my-agent --force
```

This removes: (1) the agent directory `agents/{module_name}/`, (2) the test directory `tests/{module_name}/`, (3) the import and `AgentRegistryEntry` in `agents/registry.py`.

You can also delete an agent interactively via **Step 6** in the [03_scaffold_agent.ipynb](../notebooks/03_scaffold_agent.ipynb) notebook.

> **Note:** This only removes the agent from the codebase. To also delete the agent from Azure AI Foundry, use the portal or the SDK.

**How do I add more tools to my agent?**

Create new Python files in `agents/{module_name}/tools/`, define functions and a `TOOLS` list, then update `agents/{module_name}/tools/__init__.py` to aggregate them into a combined `TOOLS` export.

**How do I change the model after creation?**

Edit `agents/{module_name}/config.py` and update the `agent_model` field's default value. You can also override it via the `AGENT_MODEL` environment variable.

**How do I enable knowledge source integration?**

Set `knowledge_source_enabled: bool = True` in your agent's config class, then implement the corresponding function in the `integrations/` directory.

**How do I enable GitHub MCP for my agent?**

Set `github_enabled: bool = True` and `github_project_connection_id: str = "your-connection-id"` in your agent's config class, or set `GITHUB_ENABLED=true` and `GITHUB_PROJECT_CONNECTION_ID=...` as environment variables. The GitHub MCP connection must already be configured in your Azure AI Foundry project.

**Can I scaffold multiple agents at once?**

Not directly. Run the script once per agent. Each invocation is independent and idempotent — it will refuse to overwrite an existing agent.

## Troubleshooting

| Error Message | Cause | Resolution |
|---------------|-------|------------|
| `Invalid agent name '...' Must be lowercase kebab-case` | Name contains uppercase, underscores, spaces, or invalid characters | Use lowercase letters, numbers, and hyphens only: `my-agent-v2` |
| `Agent name exceeds maximum length of 50 characters` | Name is too long | Choose a shorter name (50 chars max) |
| `Agent name '...' is a Python reserved word` | Name maps to a Python keyword when converted to snake_case | Choose a different name that isn't a Python keyword |
| `Agent '...' already exists at agents/...` | Agent directory already exists | Choose a different name or delete the existing agent first |
| `Test directory already exists at tests/...` | Test directory conflicts | Remove the orphaned test directory or use a different name |
| `Agent '...' is already registered in agents/registry.py` | Registry already has an entry for this name | Remove the existing registry entry or use a different name |
| `Input file not found: ...` | The `--from-file` path doesn't exist | Check the file path and ensure the YAML file exists |
| `Input file missing required field: 'name'` | YAML file doesn't contain a `name:` line | Add `name: your-agent-name` to the YAML file |
| `Permission denied` | Write access to `agents/` or `tests/` is restricted | Check file permissions or run from the repository root |
