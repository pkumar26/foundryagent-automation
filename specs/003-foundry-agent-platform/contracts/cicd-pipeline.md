# Contract: CI/CD Pipeline

**Feature**: 003-foundry-agent-platform  
**Files**: `.github/workflows/test.yml`, `.github/workflows/deploy.yml`  
**Consumers**: GitHub Actions, development team

---

## Test Pipeline (`test.yml`)

### Triggers

```yaml
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
```

### Stages

| Stage | Steps | Requires Azure Credentials |
|-------|-------|---------------------------|
| Lint & Format | Black --check, isort --check, flake8 | No |
| Unit Tests | `pytest tests/ -m "not integration"` | No |

### Outputs

- Test results (pass/fail)
- Coverage report (if configured)

### Gate

Must pass before merge to main. Configured as required status check in branch protection.

---

## Deploy Pipeline (`deploy.yml`)

### Triggers

```yaml
on:
  push:
    branches: [main]    # Auto-deploys to dev
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [dev, qa, prod]
      infra_tool:
        type: choice
        options: [terraform, bicep]
      use_existing_foundry:
        type: choice
        options: ['true', 'false']
        default: 'true'
      agent_target:
        type: string
        default: 'all'
```

### Permissions

```yaml
permissions:
  id-token: write    # Required for OIDC
  contents: read
```

### Stages

| # | Stage | Condition | Steps |
|---|-------|-----------|-------|
| 1 | Validate Inputs | Always | Resolve agent_target against registry; fail if unknown name |
| 2 | Provision Shared Infra | Always | Key Vault + AI Search (if enabled) via selected infra_tool |
| 3 | Provision Foundry | `use_existing_foundry == 'false'` | Create Foundry resource + project via selected infra_tool |
| 4 | Export Outputs | Always | Connection string from infra outputs OR GitHub secret |
| 5 | Deploy Agents | Always | `python scripts/deploy_agent.py --agent <name>` or `--all` |
| 6 | Integration Tests | Always | `pytest tests/ -m integration` (or per-agent marker) |

### Authentication

```yaml
- uses: azure/login@v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

### Secret Contract (per GitHub Environment)

| Secret | Scope | Usage |
|--------|-------|-------|
| `AZURE_CLIENT_ID` | Per environment | OIDC login |
| `AZURE_TENANT_ID` | Per environment | OIDC login |
| `AZURE_SUBSCRIPTION_ID` | Per environment | OIDC login |
| `FOUNDRY_PROJECT_CONNECTION_STRING` | Per environment | When `use_existing_foundry=true` |

### Environment Promotion

| Environment | Trigger | Gate |
|-------------|---------|------|
| dev | Auto on push to main | None (auto) |
| qa | Manual workflow_dispatch | None |
| prod | Manual workflow_dispatch | GitHub Environment approval (required reviewers) |

### Terraform Integration

```yaml
- uses: hashicorp/setup-terraform@v3
- run: terraform init -backend-config=...
- run: terraform apply -auto-approve -var-file=envs/${{ inputs.environment }}.tfvars
  env:
    ARM_USE_OIDC: true
    ARM_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
    ARM_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
    ARM_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

### Bicep Integration

```yaml
- uses: azure/arm-deploy@v2
  with:
    scope: subscription
    region: ${{ vars.AZURE_REGION }}
    template: infra/bicep/main.bicep
    parameters: infra/bicep/parameters/${{ inputs.environment }}.bicepparam
```

### Output Extraction

| Mode | Source | Variable |
|------|--------|----------|
| `use_existing_foundry=true` | GitHub secret `FOUNDRY_PROJECT_CONNECTION_STRING` | Set as env var for deploy step |
| `use_existing_foundry=false` (Terraform) | `terraform output -raw project_connection_string` | Set as env var for deploy step |
| `use_existing_foundry=false` (Bicep) | ARM deployment output `projectConnectionString` | Set as env var for deploy step |

### Agent Target Resolution

| Input | Resolution |
|-------|-----------|
| `all` | Load all names from registry via `python -c "from agents.registry import REGISTRY; print(' '.join(e.name for e in REGISTRY.list_agents()))"` |
| `<name>` | Validate exists in registry; fail with available names if not |

### Error Handling

- Stage 1 failure (invalid agent name): Pipeline stops immediately
- Stage 2-3 failure (infra): Pipeline stops — no agent deployment without infra
- Stage 5 failure (agent deploy): Reported per-agent, pipeline continues for other agents but marks overall as failed
- Stage 6 failure (tests): Pipeline marks as failed, blocks promotion
