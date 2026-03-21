# MCP & External Tools Integration Guide

[![Azure AI Foundry](https://img.shields.io/badge/Azure%20AI-Foundry-0078D4?logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/en-us/products/ai-services)
[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.x-6BA539?logo=openapiinitiative&logoColor=white)](https://www.openapis.org/)

This guide covers connecting agents to external services — GitHub, Azure, Bing, and any API with an OpenAPI spec — using the Azure AI Foundry SDK's built-in tool types.

## Overview

Beyond [custom Python tools](custom-tools-guide.md), the SDK supports several built-in tool types for connecting to external services:

| Tool Type | Use Case | Auth Model |
|-----------|----------|------------|
| **OpenApiTool** | Any REST API with an OpenAPI/Swagger spec | Anonymous, Connection, or Managed Identity |
| **AzureAISearchTool** | Search over your own data in Azure AI Search | Connection ID |
| **BingGroundingTool** | Web search via Bing for grounding answers | Connection ID |
| **CodeInterpreterTool** | Run Python code in a sandboxed environment | None (built-in) |
| **ConnectedAgentTool** | Chain to another deployed agent | Agent ID |

These tools are server-side — the SDK sends the tool definitions to Azure, and Foundry executes them. No local Python function is needed.

## Architecture: How Tools Plug In

```
agents/
├── _base/
│   └── integrations/               # Shared integration modules
│       ├── __init__.py
│       └── github_mcp.py           # Canonical GitHub OpenAPI spec + tool
└── code_helper/
    ├── tools/                      # Local Python tools (FunctionTool)
    │   ├── __init__.py             # Exports TOOLS list
    │   └── sample_tool.py          # greet_user function
    └── integrations/               # Agent-specific re-exports
        ├── __init__.py
        ├── github_mcp.py           # Re-exports from _base
        └── knowledge.py            # Azure AI Search tool
```

The agent factory (`agents/_base/agent_factory.py`) merges both sources:

1. Collects `FunctionTool` instances from `tools/`
2. Conditionally appends integration tools from `integrations/`
3. Passes all tool definitions to `create_agent()` / `update_agent()`

## GitHub MCP via OpenAPI

GitHub exposes a REST API with an OpenAPI spec. You can connect your agent to GitHub using `OpenApiTool`.

### Step 1: Set Up a Connection in Azure AI Foundry

Before using any connection-authenticated tool, create a **Custom keys** connection in your Azure AI Foundry project:

1. Go to **Azure AI Foundry portal** → your project → **Management center** → **Connected resources**
2. Click **+ New connection** → select **Custom keys** (under "Other resource types")
3. Enter the following:
   - **Connection name**: `github-mcp` (or any name you prefer)
   - **key**: `Authorization` (must match the `name` field in the OpenAPI `securitySchemes`)
   - **value**: `Bearer <your-github-pat>` (replace with your actual GitHub Personal Access Token — the `Bearer ` prefix is **required**)
4. Save — note the **Connection ID** shown in the connection details

The Connection ID follows this format:

```
/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<foundry-account>/projects/<project>/connections/<connection-name>
```

> **Important**: The connection must be **Custom keys** type (not "API key"). The key name `Authorization` must exactly match the `name` field in the OpenAPI spec's `securitySchemes`. The value must include the word `Bearer` followed by a space before the token.

### Step 2: Define the OpenAPI Spec

Create an OpenAPI spec for the GitHub endpoints your agent needs. **Critical requirements**:

- Include a `securitySchemes` section with type `apiKey` (even for Bearer tokens)
- The `name` field in `securitySchemes` must match the key name in your connection (e.g. `Authorization`)
- Include a top-level `security` section referencing the scheme
- Every operation must have a unique `operationId` (letters, `-`, and `_` only)

```python
GITHUB_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "GitHub API", "version": "1.0.0"},
    "servers": [{"url": "https://api.github.com"}],
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
            }
        }
    },
    "security": [{"bearerAuth": []}],
    "paths": {
        "/users/{username}/repos": {
            "get": {
                "operationId": "listUserRepos",
                "summary": "List repositories for a user",
                "parameters": [
                    {"name": "username", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "sort", "in": "query", "schema": {"type": "string", "enum": ["created", "updated", "pushed", "full_name"]}},
                    {"name": "per_page", "in": "query", "schema": {"type": "integer", "default": 30}},
                ],
                "responses": {"200": {"description": "List of repositories"}},
            }
        },
        "/repos/{owner}/{repo}": {
            "get": {
                "operationId": "getRepo",
                "summary": "Get a repository",
                "parameters": [
                    {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "responses": {"200": {"description": "Repository details"}},
            }
        },
        "/repos/{owner}/{repo}/issues": {
            "get": {
                "operationId": "listIssues",
                "summary": "List repository issues",
                "parameters": [
                    {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "state", "in": "query", "schema": {"type": "string", "enum": ["open", "closed", "all"]}},
                ],
                "responses": {"200": {"description": "List of issues"}},
            }
        },
        "/repos/{owner}/{repo}/pulls": {
            "get": {
                "operationId": "listPullRequests",
                "summary": "List pull requests",
                "parameters": [
                    {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "state", "in": "query", "schema": {"type": "string", "enum": ["open", "closed", "all"]}},
                ],
                "responses": {"200": {"description": "List of pull requests"}},
            }
        },
    },
}
```

Or load from a YAML/JSON file:

```python
import json
from pathlib import Path

spec = json.loads(Path("specs/github-openapi.json").read_text())
```

> **Why `apiKey` type instead of `http/bearer`?** Azure AI Foundry maps connection credentials to the request using the `name` and `in` fields from `securitySchemes`. The `http` scheme type is not supported for Custom keys connections — use `apiKey` with `"in": "header"` instead, and store `Bearer <token>` as the connection value.

### Step 3: Implement the Integration

Replace the stub in `agents/code_helper/integrations/github_mcp.py` (the actual implementation is already provided — see `agents/code_helper/integrations/github_mcp.py` for the full code). The key implementation pattern:

```python
"""GitHub MCP integration for the code-helper agent."""

from azure.ai.agents.models import (
    OpenApiTool,
    OpenApiConnectionAuthDetails,
    OpenApiConnectionSecurityScheme,
)

from agents._base.config import FoundryBaseConfig

GITHUB_SPEC = { ... }  # Full spec from Step 2 above


def get_github_mcp_tool(config: FoundryBaseConfig):
    """Return a GitHub OpenAPI tool, or None if disabled."""
    if not getattr(config, "github_mcp_enabled", False):
        return None

    connection_id = getattr(config, "github_mcp_connection_id", "")
    if not connection_id:
        raise ValueError(
            "GITHUB_MCP_CONNECTION_ID is required when GITHUB_MCP_ENABLED=true. "
            "Create a connection in Azure AI Foundry and set the connection ID."
        )

    auth = OpenApiConnectionAuthDetails(
        security_scheme=OpenApiConnectionSecurityScheme(
            connection_id=connection_id,
        )
    )

    return OpenApiTool(
        name="github",
        description="Query GitHub repositories — list issues, pull requests, and more.",
        spec=GITHUB_SPEC,
        auth=auth,
    )
```

> **Tip**: The canonical implementation lives in `agents/_base/integrations/github_mcp.py`. Both `code_helper` and `doc_assistant` re-export it via `from agents._base.integrations.github_mcp import get_github_mcp_tool`. New agents scaffolded with `create_agent.py` use the same import automatically.

### Step 4: Update Config

Add the connection ID field to your agent's config:

```python
# agents/code_helper/config.py
class CodeHelperConfig(FoundryBaseConfig):
    agent_name: str = "code-helper"
    agent_model: str = "gpt-4o"
    agent_instructions_path: str = "agents/code_helper/instructions.md"

    # GitHub integration
    github_mcp_enabled: bool = False
    github_mcp_connection_id: str = ""  # Azure AI Foundry connection ID
```

### Step 5: Set Environment Variables and Deploy

```bash
# .env
GITHUB_MCP_ENABLED=true
GITHUB_MCP_CONNECTION_ID=/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<account>/projects/<project>/connections/github-mcp

# Deploy
uv run python scripts/deploy_agent.py --agent code-helper
```

> **Finding your Connection ID**: Run `uv run python -c "from azure.ai.projects import AIProjectClient; from azure.identity import DefaultAzureCredential; c = AIProjectClient(endpoint='<your-endpoint>', credential=DefaultAzureCredential()); [print(f'{conn.name}: {conn.id}') for conn in c.connections.list()]"`

### Step 6: Test It

In notebook `02_build_and_run_agent.ipynb`, change the message to:

```python
content = "List the open issues in the pkumar26/foundryagent-automation repo"
```

## Azure AI Search (Knowledge Source)

Connect your agent to an Azure AI Search index so it can search over your own documents.

### Step 1: Set Up Azure AI Search

1. Create an **Azure AI Search** resource (the Bicep/Terraform in `infra/` can provision this when `enable_knowledge_source=true`)
2. Create an index and populate it with your documents
3. Create a **connection** in your Azure AI Foundry project pointing to the search resource

### Step 2: Implement the Integration

Replace the stub in `agents/code_helper/integrations/knowledge.py`:

```python
"""Knowledge source integration via Azure AI Search for the code-helper agent."""

from azure.ai.agents.models import AzureAISearchTool

from agents._base.config import FoundryBaseConfig


def get_knowledge_tool(config: FoundryBaseConfig):
    """Return an Azure AI Search tool, or None if disabled.

    Args:
        config: Agent configuration with knowledge_source_enabled flag.

    Returns:
        AzureAISearchTool when enabled, None when disabled.
    """
    if not getattr(config, "knowledge_source_enabled", False):
        return None

    connection_id = getattr(config, "azure_ai_search_connection_id", "")
    index_name = getattr(config, "azure_ai_search_index_name", "")

    if not connection_id or not index_name:
        raise ValueError(
            "AZURE_AI_SEARCH_CONNECTION_ID and AZURE_AI_SEARCH_INDEX_NAME are required "
            "when KNOWLEDGE_SOURCE_ENABLED=true."
        )

    return AzureAISearchTool(
        index_connection_id=connection_id,
        index_name=index_name,
    )
```

### Step 3: Update Config and Deploy

```python
# agents/code_helper/config.py
class CodeHelperConfig(FoundryBaseConfig):
    # ...existing fields...
    knowledge_source_enabled: bool = False
    azure_ai_search_connection_id: str = ""
    azure_ai_search_index_name: str = ""
```

```bash
# .env
KNOWLEDGE_SOURCE_ENABLED=true
AZURE_AI_SEARCH_CONNECTION_ID=/subscriptions/.../connections/ai-search
AZURE_AI_SEARCH_INDEX_NAME=my-docs-index

uv run python scripts/deploy_agent.py --agent code-helper
```

## Bing Web Search (Grounding)

Give your agent access to real-time web search results from Bing.

### Step 1: Create a Bing Connection

1. Create a **Bing Search** resource in Azure
2. Create a **connection** in your Azure AI Foundry project for the Bing resource
3. Note the **Connection ID**

### Step 2: Add a Bing Tool

```python
# agents/code_helper/integrations/bing.py
from azure.ai.agents.models import BingGroundingTool

from agents._base.config import FoundryBaseConfig


def get_bing_tool(config: FoundryBaseConfig):
    """Return a Bing grounding tool, or None if disabled."""
    connection_id = getattr(config, "bing_connection_id", "")
    if not connection_id:
        return None

    return BingGroundingTool(connection_id=connection_id)
```

Add to config:

```python
bing_connection_id: str = ""  # Set via BING_CONNECTION_ID env var
```

Then register it in the factory by adding it to `_append_integration_tools()` or by updating your agent's tools `__init__.py`.

## Code Interpreter

Let your agent execute Python code in a sandboxed environment:

```python
from azure.ai.agents.models import CodeInterpreterTool

# No auth needed — it's a built-in Azure service
tool = CodeInterpreterTool()
```

Add it to your agent's `TOOLS` list in `tools/__init__.py`:

```python
from azure.ai.agents.models import CodeInterpreterTool

TOOLS = [
    # ...your existing tools...
    CodeInterpreterTool(),
]
```

## Connected Agents (Agent-to-Agent)

Chain agents together — one agent can call another deployed agent as a tool:

```python
from azure.ai.agents.models import ConnectedAgentTool

# The target agent must already be deployed
tool = ConnectedAgentTool(
    id="asst_abc123",               # Deployed agent ID
    name="doc-assistant",            # Display name
    description="Search and summarise documentation",
)
```

## OpenAPI Tool: Any REST API

The `OpenApiTool` pattern works for any API with an OpenAPI spec — not just GitHub. Here's the general pattern:

### Anonymous Auth (Public APIs)

```python
from azure.ai.agents.models import OpenApiTool, OpenApiAnonymousAuthDetails

tool = OpenApiTool(
    name="weather",
    description="Get current weather data",
    spec=weather_openapi_spec,  # dict or JSON string
    auth=OpenApiAnonymousAuthDetails(),
)
```

### Connection Auth (API Keys / Tokens)

For connection-authenticated tools, your OpenAPI spec **must** include `securitySchemes` and a `security` section. Without these, the API key won't be included in requests.

```python
from azure.ai.agents.models import (
    OpenApiTool,
    OpenApiConnectionAuthDetails,
    OpenApiConnectionSecurityScheme,
)

# Your spec must include securitySchemes — example for Bearer token:
my_api_spec = {
    "openapi": "3.0.0",
    "info": {"title": "My API", "version": "1.0.0"},
    "servers": [{"url": "https://my-api.example.com"}],
    "components": {
        "securitySchemes": {
            "apiKeyAuth": {
                "type": "apiKey",
                "name": "Authorization",  # Must match the key name in your connection
                "in": "header",
            }
        }
    },
    "security": [{"apiKeyAuth": []}],
    "paths": { ... },
}

tool = OpenApiTool(
    name="my-api",
    description="Query the internal API",
    spec=my_api_spec,
    auth=OpenApiConnectionAuthDetails(
        security_scheme=OpenApiConnectionSecurityScheme(
            connection_id="your-foundry-connection-id",
        )
    ),
)
```

> **Connection setup**: Create a **Custom keys** connection in Azure AI Foundry. Set the **key** to match the `name` field in your `securitySchemes` (e.g. `Authorization`). For Bearer tokens, set the **value** to `Bearer <token>` (include the `Bearer ` prefix).

### Managed Identity Auth (Azure Services)

```python
from azure.ai.agents.models import (
    OpenApiTool,
    OpenApiManagedAuthDetails,
    OpenApiManagedSecurityScheme,
)

tool = OpenApiTool(
    name="azure-service",
    description="Call an Azure service",
    spec=azure_api_spec,
    auth=OpenApiManagedAuthDetails(
        security_scheme=OpenApiManagedSecurityScheme(
            audience="https://management.azure.com/.default",
        )
    ),
)
```

### Multiple Endpoints in One Tool

Add additional API definitions to an existing tool:

```python
tool = OpenApiTool(
    name="github-issues",
    description="List GitHub issues",
    spec=issues_spec,
    auth=auth,
)

# Add more endpoints to the same tool
tool.add_definition(
    name="github-pulls",
    description="List GitHub pull requests",
    spec=pulls_spec,
)
```

## Integration Points in This Repo

The platform has two built-in integration hooks per agent:

| Hook | Config Flag | File | Purpose |
|------|-------------|------|---------|
| Knowledge source | `knowledge_source_enabled` | `integrations/knowledge.py` | Azure AI Search |
| GitHub MCP | `github_mcp_enabled` | `integrations/github_mcp.py` | GitHub API via OpenAPI |

The agent factory calls these automatically during deploy. To add more integration hooks (e.g., Bing, Code Interpreter), either:

1. **Simple**: Add the tool directly to your `tools/__init__.py` TOOLS list
2. **With feature flag**: Add a new integration file + config flag, and extend `_append_integration_tools()` in `agents/_base/agent_factory.py`

## Environment Variables Reference

```bash
# GitHub OpenAPI integration
GITHUB_MCP_ENABLED=true
GITHUB_MCP_CONNECTION_ID=/subscriptions/<sub>/resourceGroups/<rg>/providers/...

# Azure AI Search integration
KNOWLEDGE_SOURCE_ENABLED=true
AZURE_AI_SEARCH_CONNECTION_ID=/subscriptions/<sub>/resourceGroups/<rg>/providers/...
AZURE_AI_SEARCH_INDEX_NAME=my-index

# Bing grounding (add to your config class)
BING_CONNECTION_ID=/subscriptions/<sub>/resourceGroups/<rg>/providers/...
```

## Checklist

- [ ] **Custom keys** connection created in Azure AI Foundry portal (key name matches `securitySchemes`, value includes `Bearer ` prefix for tokens)
- [ ] Connection ID added to agent config class and `.env`
- [ ] OpenAPI spec includes `securitySchemes` and `security` sections
- [ ] Integration stub replaced with real implementation
- [ ] Agent instructions updated to mention the tool names
- [ ] Feature flag set to `true` in `.env`
- [ ] Agent redeployed with `deploy_agent.py`
- [ ] Tested with a relevant prompt in notebook or terminal
