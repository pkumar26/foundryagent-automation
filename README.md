# Foundry Agent Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Azure AI Foundry](https://img.shields.io/badge/Azure%20AI-Foundry-0078D4?logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/en-us/products/ai-services)
[![Terraform](https://img.shields.io/badge/Terraform-%3E%3D1.5-7B42BC?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![Bicep](https://img.shields.io/badge/Bicep-IaC-0078D4?logo=microsoftazure&logoColor=white)](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/features/actions)
![GitHub stars](https://img.shields.io/github/stars/pkumar26/foundryagent-automation?style=social)
![GitHub forks](https://img.shields.io/github/forks/pkumar26/foundryagent-automation?style=social)
![GitHub issues](https://img.shields.io/github/issues/pkumar26/foundryagent-automation)](https://github.com/pkumar26/foundryagent-automation/issues)
![GitHub last commit](https://img.shields.io/github/last-commit/pkumar26/foundryagent-automation)](https://github.com/pkumar26/foundryagent-automation/commits)
![Repo size](https://img.shields.io/github/repo-size/pkumar26/foundryagent-automation)

A production-grade, multi-agent platform built on the **Azure AI Foundry Agent Service SDK**. Each agent is self-contained, independently deployable, and managed through a central registry. Deploy one agent or many, across dev/qa/prod environments, using automated CI/CD with GitHub Actions and your choice of Terraform or Bicep for infrastructure.

## Architecture

```
agents/
├── _base/              # Shared: config, client, factory, run lifecycle, tools
├── code_helper/        # Agent 1: coding assistant with greeting tool
├── doc_assistant/      # Agent 2: documentation helper with summarisation tool
└── registry.py         # Central agent registry

infra/
├── terraform/          # Terraform IaC (azurerm >= 4.0)
└── bicep/              # Bicep IaC (equivalent Azure resources)

tests/                  # Unit + integration tests mirroring agents/ structure
notebooks/              # Interactive onboarding guides
scripts/                # CLI deploy script
.github/workflows/      # CI/CD pipelines (test + deploy)
```

## Decision Guide

| Question | Option A | Option B |
|----------|----------|----------|
| **Foundry project** | Use existing (`use_existing_foundry=true`) | Provision new (`use_existing_foundry=false`) |
| **Infrastructure** | Terraform (`infra/terraform/`) | Bicep (`infra/bicep/`) |
| **Deploy target** | Single agent (`--agent <name>`) | All agents (`--all`) |

## Quick Start

### Prerequisites

- Python 3.11+
- Azure CLI authenticated (`az login`)
- An Azure AI Foundry project connection string

### Setup

```bash
git clone <repo-url>
cd foundryagent-automation

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your FOUNDRY_PROJECT_CONNECTION_STRING
```

### Deploy Your First Agent

```bash
python scripts/deploy_agent.py --agent code-helper
```

### Deploy All Agents

```bash
python scripts/deploy_agent.py --all
```

### Run Tests

```bash
pip install -r requirements-dev.txt

# Unit tests (no Azure credentials needed)
pytest tests/ -m "not integration" -v

# Integration tests (requires FOUNDRY_PROJECT_CONNECTION_STRING)
pytest tests/ -m integration -v

# Tests for a specific agent
pytest tests/ -m code_helper -v
```

## Adding a New Agent

1. Create folder: `agents/<new_agent>/` with `config.py`, `instructions.md`, `tools/`, `integrations/`
2. Add one entry to `agents/registry.py`
3. Deploy: `python scripts/deploy_agent.py --agent <new-agent>`

Zero changes to existing agents or shared code required.

## Notebooks

Interactive onboarding for developers new to Azure AI Foundry:

- **[01_setup_and_connect.ipynb](notebooks/01_setup_and_connect.ipynb)** — Connect to Foundry (existing or new)
- **[02_build_and_run_agent.ipynb](notebooks/02_build_and_run_agent.ipynb)** — Create, run, and interact with an agent

## CI/CD

| Pipeline | Trigger | Purpose |
|----------|---------|---------|
| `test.yml` | PR + push to main | Lint (Black, isort, flake8) + unit tests |
| `deploy.yml` | Push to main (dev auto) / manual dispatch (qa/prod) | Infra provisioning + agent deployment + integration tests |

Authentication uses OIDC (Workload Identity Federation) — no client secrets.

## Infrastructure

Both Terraform and Bicep produce identical environments:

- Resource Group
- Key Vault (RBAC-enabled)
- Foundry Resource (CognitiveServices/AIServices) — conditional
- AI Search — conditional on `enable_knowledge_source`
- RBAC role assignments (Contributor, Cognitive Services User, Key Vault Secrets User)

## Specification

Full design documents: [`specs/003-foundry-agent-platform/`](specs/003-foundry-agent-platform/)
