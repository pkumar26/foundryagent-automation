# Foundry Agent Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-package%20manager-DE5FE9?logo=uv&logoColor=white)](https://docs.astral.sh/uv/)
[![Azure AI Foundry](https://img.shields.io/badge/Azure%20AI-Foundry-0078D4?logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/en-us/products/ai-services)
[![Terraform](https://img.shields.io/badge/Terraform-%3E%3D1.5-7B42BC?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![Bicep](https://img.shields.io/badge/Bicep-IaC-0078D4?logo=microsoftazure&logoColor=white)](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/features/actions)
![GitHub stars](https://img.shields.io/github/stars/pkumar26/foundryagent-automation?style=social)
![GitHub forks](https://img.shields.io/github/forks/pkumar26/foundryagent-automation?style=social)
[![GitHub issues](https://img.shields.io/github/issues/pkumar26/foundryagent-automation)](https://github.com/pkumar26/foundryagent-automation/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/pkumar26/foundryagent-automation)](https://github.com/pkumar26/foundryagent-automation/commits)
![Repo size](https://img.shields.io/github/repo-size/pkumar26/foundryagent-automation)

A production-grade, multi-agent platform built on the **Azure AI Foundry Agent Service SDK**. Each agent is self-contained, independently deployable, and managed through a central registry. Deploy one agent or many, across dev/qa/prod environments, using automated CI/CD with GitHub Actions and your choice of Terraform or Bicep for infrastructure.

## Architecture

```
agents/
├── _base/              # Shared: config, client, factory, run lifecycle, tools
│   └── integrations/   # Shared integration modules (knowledge source, etc.)
├── code_helper/        # Agent 1: coding assistant with greeting tool
├── doc_assistant/      # Agent 2: documentation helper with summarisation tool
└── registry.py         # Central agent registry

infra/
├── terraform/          # Terraform IaC (azurerm >= 4.0)
└── bicep/              # Bicep IaC (equivalent Azure resources)

tests/                  # Unit + integration tests mirroring agents/ structure
notebooks/              # Interactive onboarding guides
scripts/                # CLI deploy + agent scaffolding
├── deploy_agent.py     # CLI deploy script
├── create_agent.py     # CLI agent scaffolding
└── delete_agent.py     # CLI agent removal
docs/                   # Guides and reference documentation
.github/workflows/      # CI/CD pipelines (test + deploy)
```

## Decision Guide

| Question | Option A | Option B |
|----------|----------|----------|
| **Foundry project** | Use existing (`use_existing_foundry=true`) | Provision new (`use_existing_foundry=false`) |
| **Infrastructure** | Terraform (`infra/terraform/`) | Bicep (`infra/bicep/`) |
| **Deploy target** | Single agent (`--name <name>`) | All agents (`--all`) |

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (install: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Azure CLI authenticated (`az login`)
- An Azure AI Foundry project endpoint URL

### Setup

```bash
git clone <repo-url>
cd foundryagent-automation

uv sync

cp .env.example .env
# Edit .env with your AZURE_AI_PROJECT_ENDPOINT
```

### Deploy Your First Agent

```bash
uv run python scripts/deploy_agent.py --name code-helper
```

### Deploy All Agents

```bash
uv run python scripts/deploy_agent.py --all
```

### Run Tests

```bash
uv sync --group dev

# Unit tests (no Azure credentials needed)
uv run pytest tests/ -m "not integration" -v

# Integration tests (requires AZURE_AI_PROJECT_ENDPOINT)
# pydantic-settings loads .env from the working directory automatically.
# When running from a different directory, export the variable manually:
export AZURE_AI_PROJECT_ENDPOINT=$(grep AZURE_AI_PROJECT_ENDPOINT .env | cut -d= -f2-)
uv run pytest tests/ -m integration -v

# Tests for a specific agent
uv run pytest tests/ -m code_helper -v
```

## Adding a New Agent

### Automated (Recommended)

```bash
# Scaffold a new agent with one command
uv run python scripts/create_agent.py --name my-agent

# Or specify a model
uv run python scripts/create_agent.py --name my-agent --model gpt-4o-mini

# Or use a YAML input file
uv run python scripts/create_agent.py --from-file agent-config.yaml
```

This generates the full agent directory (`agents/my_agent/`), test stubs (`tests/my_agent/`), and registry entry — ready to deploy immediately.

See the [Scaffolding Guide](docs/scaffolding-guide.md) for YAML format, customisation, FAQ, and troubleshooting.

### Delete an Agent

```bash
# Remove an agent from the codebase (with confirmation prompt)
uv run python scripts/delete_agent.py --name my-agent

# Skip confirmation
uv run python scripts/delete_agent.py --name my-agent --force
```

This removes the agent directory, test directory, and registry entry.

### Manual

1. Create folder: `agents/<new_agent>/` with `config.py`, `instructions.md`, `tools/`, `integrations/`
2. Add one entry to `agents/registry.py`
3. Deploy: `uv run python scripts/deploy_agent.py --name <new-agent>`

Zero changes to existing agents or shared code required.

## Notebooks

Interactive onboarding for developers new to Azure AI Foundry:

- **[01_setup_and_connect.ipynb](notebooks/01_setup_and_connect.ipynb)** — Connect to Foundry (existing or new)
- **[02_build_and_run_agent.ipynb](notebooks/02_build_and_run_agent.ipynb)** — Create, run, and interact with an agent
- **[03_scaffold_agent.ipynb](notebooks/03_scaffold_agent.ipynb)** — Scaffold, deploy, and delete an agent end-to-end

## Programmatic API

The `agents` package exposes a public API for scripting and notebook use:

```python
from agents import REGISTRY, create_or_update_agent, run_agent, AgentRunError

# List registered agents
for name in REGISTRY:
    print(name)

# Deploy an agent
cfg = REGISTRY["code-helper"]
agent = create_or_update_agent(cfg)

# Run a conversation turn
response = run_agent(agent.id, "Explain Python decorators")
print(response)
```

| Symbol | Description |
|--------|-------------|
| `REGISTRY` | `dict[str, FoundryBaseConfig]` — all registered agent configs |
| `create_or_update_agent` | Idempotently deploy an agent to Azure AI Foundry |
| `run_agent` | Create a thread, run a prompt, and return the response |
| `AgentRunError` | Raised when a run fails or is cancelled |

## Agent Documentation

- **[Code Helper](agents/code_helper/README.md)** — General-purpose coding assistant for debugging, code review, and technical Q&A
- **[Doc Assistant](agents/doc_assistant/README.md)** — Documentation specialist for READMEs, API docs, and technical writing

## Guides

- **[Infrastructure Guide](docs/infrastructure-guide.md)** — Deploy Azure infrastructure with Terraform or Bicep (setup, parameters, CI/CD, troubleshooting)
- **[Scaffolding Guide](docs/scaffolding-guide.md)** — YAML format, customisation, and FAQ for agent scaffolding
- **[Custom Tools Guide](docs/custom-tools-guide.md)** — How to write, test, and deploy custom Python tool functions

## CI/CD

| Pipeline | Trigger | Purpose |
|----------|---------|---------|
| `test.yml` | PR + push to main | Lint (Black, isort, flake8) + unit tests |
| `deploy.yml` | Push to main (dev auto) / manual dispatch (qa/prod) | Infra provisioning + agent deployment + integration tests |
| `create-agent.yml` | Manual dispatch | Scaffold new agent + open PR |

### Workflow Dispatch Inputs

**deploy.yml** (manual dispatch for qa/prod):

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `environment` | yes | — | Target environment: `dev`, `qa`, or `prod` |
| `infra_tool` | yes | `terraform` | IaC tool: `terraform` or `bicep` |
| `use_existing_foundry` | yes | `true` | Use an existing Foundry project or provision new |
| `agent_target` | yes | `all` | Agent to deploy: `all` or a specific agent name |

**create-agent.yml** (scaffold a new agent):

| Input | Required | Description |
|-------|----------|-------------|
| `agent_name` | yes | Kebab-case name for the new agent (e.g. `my-agent`) |

Authentication uses OIDC (Workload Identity Federation) — no client secrets. When using an existing Foundry project, the CI/CD service principal also needs the **Azure AI Developer** role on the Foundry resource — see the [Infrastructure Guide](docs/infrastructure-guide.md#rbac-roles) for setup instructions.

## Integrations

The platform supports per-agent opt-in integrations — enable them in each agent's `config.py`:

| Integration | config.py Property | Additional Properties | Description |
|---|---|---|---|
| **Knowledge Source** (Azure AI Search) | `knowledge_source_enabled = True` | `azure_ai_search_connection_id`, `azure_ai_search_index_name` | Ground agent responses in your own data |
| **Code Interpreter** | `code_interpreter_enabled = True` | — | Let the agent execute Python code |
| **Web Search** | `web_search_enabled = True` | — | Enable web search grounding |
| **GitHub MCP** | `github_enabled = True` | `github_project_connection_id` | Attach the GitHub MCP server configured in your Foundry project |

Each agent controls its own flags — set `github_enabled: bool = True` in one agent's config without affecting others. The `.env` file is for shared infrastructure only (endpoint, environment, key vault). See the [Custom Tools Guide](docs/custom-tools-guide.md) for details.

## Infrastructure

Both Terraform and Bicep produce identical environments:

- Resource Group
- Key Vault (RBAC-enabled)
- Foundry Resource (CognitiveServices/AIServices) — conditional
- AI Search — conditional on `enable_knowledge_source`
- RBAC role assignments (Contributor, Cognitive Services User, Key Vault Secrets User)

See the **[Infrastructure Guide](docs/infrastructure-guide.md)** for step-by-step deployment instructions, parameter reference, CI/CD setup, and troubleshooting.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
