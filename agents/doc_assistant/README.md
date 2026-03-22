# Documentation Assistant Agent

![Agent](https://img.shields.io/badge/agent-doc--assistant-purple)
![Model](https://img.shields.io/badge/model-gpt--4o-green)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)

A specialised documentation assistant that helps developers create, improve, and maintain technical documentation.

## Purpose

Doc Assistant handles documentation-centric tasks — drafting READMEs, API docs, setup guides, changelogs, docstrings, and improving existing docs for clarity and completeness.

## Capabilities

| Capability | Description |
|---|---|
| README drafting | Generate project READMEs with proper structure and formatting |
| API documentation | Produce endpoint references, request/response examples |
| Setup guides | Write installation, configuration, and quickstart guides |
| Content summarisation | Condense technical content into concise documentation |
| Doc improvement | Review existing docs and suggest clarity/completeness fixes |
| GitHub queries | Browse repos and files for context (via Foundry MCP) |

## Tools

| Tool | Function | Description |
|---|---|---|
| `summarise_text` | `agents/doc_assistant/tools/sample_tool.py` | Summarises text to a given number of sentences |

## Configuration

| Setting | Env Variable | Default | Description |
|---|---|---|---|
| Agent name | — | `doc-assistant` | Identifier used in the registry |
| Model | — | `gpt-4o` | Azure OpenAI deployment |
| Knowledge source | `KNOWLEDGE_SOURCE_ENABLED` | `false` | Enable Azure AI Search knowledge base |
| Search connection | `AZURE_AI_SEARCH_CONNECTION_ID` | — | AI Foundry connection ID for AI Search |
| Search index | `AZURE_AI_SEARCH_INDEX_NAME` | — | Index name in Azure AI Search |

## File Structure

```
agents/doc_assistant/
├── __init__.py
├── config.py              # DocAssistantConfig (extends FoundryBaseConfig)
├── instructions.md        # System prompt
├── integrations/
│   ├── __init__.py
│   └── knowledge.py       # Azure AI Search integration
└── tools/
    ├── __init__.py
    └── sample_tool.py     # summarise_text function
```

## Quick Start

```bash
# Deploy
uv run python scripts/deploy_agent.py --agent doc-assistant

# Run interactively
uv run python -m agents._base.run doc-assistant
```

## Testing

```bash
# Unit tests
uv run pytest tests/doc_assistant/ -v

# Skip integration tests
uv run pytest tests/doc_assistant/ -v -m "not integration"
```
