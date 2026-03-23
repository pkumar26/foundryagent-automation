# foundryagent-automation Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-22

## Active Technologies
- Python 3.11+ + `azure-ai-projects>=2.0.0`, `azure-identity>=1.15.0`, `pydantic-settings>=2.0.0`, `openai` (transitive via azure-ai-projects v2)
- Serverless agents in Azure AI Foundry (AIProjectClient)
- Agent scaffolding: Python standard library only (argparse, pathlib, textwrap, re); pydantic-settings (for generated config classes)

## Project Structure

```text
agents/          # Agent packages (_base/, code_helper/, doc_assistant/, etc.)
tests/           # Unit + integration tests mirroring agents/ structure
scripts/         # CLI tools (deploy, create, delete)
infra/           # Terraform + Bicep IaC
notebooks/       # Interactive onboarding guides
docs/            # Guides and reference documentation
```

## Commands

```bash
uv sync                                          # Install dependencies
uv run pytest tests/ -m "not integration" -v     # Unit tests
uv run pytest tests/ -m integration -v           # Integration tests (requires AZURE_AI_PROJECT_ENDPOINT)
uv run python scripts/deploy_agent.py --name <agent>  # Deploy an agent
uv run python scripts/create_agent.py --name <agent>  # Scaffold a new agent
```

## Code Style

Python 3.11+: black (line-length=100), isort (profile=black), flake8

## Recent Changes
- 005-migrate-to-new-foundry: Migrated from `azure-ai-agents` (AgentsClient) to `azure-ai-projects>=2.0.0` (AIProjectClient) with new Conversations/Responses model
- 004-agent-scaffolding: CLI tool for scaffolding new agents with full directory structure, tests, and registry entry

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
