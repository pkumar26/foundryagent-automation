# Quickstart: Foundry Agent Platform

**Feature**: 003-foundry-agent-platform  
**Date**: 2026-03-18  

---

## Prerequisites

- Python 3.11+
- An Azure subscription
- Azure CLI installed and authenticated (`az login`)
- A Foundry project connection string (see "Connect to Foundry" below)
- Git

## 1. Clone and Setup

```bash
git clone <repo-url>
cd foundryagent-automation

python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set:
```env
FOUNDRY_PROJECT_CONNECTION_STRING=<your-connection-string>
ENVIRONMENT=dev
AZURE_KEY_VAULT_NAME=<your-keyvault-name>  # optional
```

**Where to find your connection string**: Azure Portal → AI Foundry → Your Project → Settings → Connection string. Copy the full value.

## 3. Deploy Your First Agent

```bash
python scripts/deploy_agent.py --agent <agent-name-1>
```

The script will:
1. Load the agent's config from `agents/<agent-name-1>/config.py`
2. Read instructions from `agents/<agent-name-1>/instructions.md`
3. Register tools from `agents/<agent-name-1>/tools/`
4. Create or update the agent in your Foundry project (idempotent)

## 4. Test the Agent

Open a Python shell or use the notebook `notebooks/02_build_and_run_agent.ipynb`:

```python
from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential

client = AgentsClient(
    endpoint="<your-connection-string>",
    credential=DefaultAzureCredential()
)

# Create thread, send message, run agent
thread = client.threads.create()
client.messages.create(thread_id=thread.id, role="user", content="Hello!")
run = client.runs.create_and_process(thread_id=thread.id, agent_id="<agent-id>")

# Get response
from azure.ai.agents.models import MessageRole
last_msg = client.messages.get_last_message_text_by_role(
    thread_id=thread.id, role=MessageRole.AGENT
)
print(last_msg.text.value)
```

## 5. Run Tests

```bash
# Unit tests (no Azure credentials needed)
pytest tests/ -m "not integration"

# Integration tests (requires FOUNDRY_PROJECT_CONNECTION_STRING)
pytest tests/ -m integration

# Tests for a specific agent only
pytest tests/ -m <agent_name_1>
```

## 6. Deploy All Agents

```bash
python scripts/deploy_agent.py --all
```

## 7. Add a New Agent

### Automated (Recommended)

```bash
python scripts/create_agent.py --name my-agent
```

See the [Scaffolding Guide](../../docs/scaffolding-guide.md) for YAML input, customisation, and FAQ.

### Manual

1. Create folder: `agents/<new-agent>/`
2. Add files: `__init__.py`, `config.py`, `instructions.md`, `tools/`, `integrations/`
3. Register in `agents/registry.py`
4. Deploy: `python scripts/deploy_agent.py --agent <new-agent>`

See [spec.md](spec.md) for full details on each file's responsibility.

## Next Steps

- **Notebooks**: Start with `notebooks/01_setup_and_connect.ipynb` for guided setup
- **Infrastructure**: See `infra/terraform/` or `infra/bicep/` for provisioning
- **CI/CD**: See `.github/workflows/deploy.yml` for automated deployment pipeline
