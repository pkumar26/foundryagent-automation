# Code Helper Agent

![Agent](https://img.shields.io/badge/agent-code--helper-blue)
![Model](https://img.shields.io/badge/model-gpt--4o-green)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)

A general-purpose coding assistant that helps developers with programming tasks, code review, debugging, and technical questions.

## Purpose

Code Helper is designed for day-to-day developer support — answering questions about languages, frameworks, and best practices, debugging errors, providing code snippets, and explaining technical concepts.

## Capabilities

| Capability | Description |
|---|---|
| Code review | Analyse code for bugs, performance, and style issues |
| Debugging | Interpret error messages and suggest fixes |
| Code generation | Provide snippets and examples in any language |
| Technical Q&A | Explain concepts, compare frameworks, recommend patterns |
| GitHub queries | Browse repos, issues, PRs, and file contents (via Foundry MCP) |

## Tools

| Tool | Function | Description |
|---|---|---|
| `greet_user` | `agents/code_helper/tools/sample_tool.py` | Greets a user by name (sample/demo tool) |

## Configuration

| Setting | Env Variable | Default | Description |
|---|---|---|---|
| Agent name | — | `code-helper` | Identifier used in the registry |
| Model | — | `gpt-4o` | Azure OpenAI deployment |
| Knowledge source | `KNOWLEDGE_SOURCE_ENABLED` | `false` | Enable Azure AI Search knowledge base |
| Search connection | `AZURE_AI_SEARCH_CONNECTION_ID` | — | AI Foundry connection ID for AI Search |
| Search index | `AZURE_AI_SEARCH_INDEX_NAME` | — | Index name in Azure AI Search |

## File Structure

```
agents/code_helper/
├── __init__.py
├── config.py              # CodeHelperConfig (extends FoundryBaseConfig)
├── instructions.md        # System prompt
├── integrations/
│   ├── __init__.py
└── tools/
    ├── __init__.py
    └── sample_tool.py     # greet_user function
```

## Quick Start

```bash
# Deploy
uv run python scripts/deploy_agent.py --agent code-helper

# Run interactively
uv run python -m agents._base.run code-helper
```

## Testing

```bash
# Unit tests
uv run pytest tests/code_helper/ -v

# Skip integration tests
uv run pytest tests/code_helper/ -v -m "not integration"
```
