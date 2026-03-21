# Research: Foundry Agent Platform

**Feature**: 003-foundry-agent-platform  
**Date**: 2026-03-18  
**Purpose**: Resolve all technical unknowns from the spec before Phase 1 design.

---

## 1. azure-ai-projects SDK — Agent Lifecycle Patterns

**Decision**: Use `AIProjectClient` from `azure.ai.projects` with `agents` sub-client for all agent operations. Use `create_and_process_run()` for built-in polling with automatic tool-call handling.

**Rationale**: The SDK provides a high-level client that handles polling, tool-call dispatch, and terminal-state detection internally. This eliminates custom polling logic for the common case while still allowing manual fallback via `runs.create()` + `runs.get()` loop for edge cases.

**Alternatives Considered**:
- Manual polling only (`runs.create()` + sleep loop): Rejected — reinvents logic the SDK already provides, and misses automatic tool-call handling.
- REST API directly: Rejected — no value over SDK; SDK handles auth, retries, and serialisation.

**Key Patterns**:

```python
# Imports
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool, ListSortOrder
from azure.identity import DefaultAzureCredential

# Client initialisation (singleton)
client = AIProjectClient.from_connection_string(
    conn_str=connection_string,
    credential=DefaultAzureCredential()
)
agents_client = client.agents

# Create agent
agent = agents_client.create_agent(
    model=model_name,
    name=agent_name,
    instructions=instructions_text,
    tools=tool_definitions  # list of FunctionTool.definitions
)

# Update agent (idempotent)
agent = agents_client.update_agent(
    agent_id=existing_agent.id,
    model=model_name,
    name=agent_name,
    instructions=instructions_text,
    tools=tool_definitions
)

# List agents (for exists-by-name check)
agents_list = agents_client.list_agents()
existing = next((a for a in agents_list.data if a.name == agent_name), None)

# Thread + run lifecycle
thread = agents_client.threads.create()
agents_client.messages.create(thread_id=thread.id, role="user", content=prompt)
run = agents_client.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
# run is terminal at this point (completed/failed/cancelled)

# Retrieve response
messages = agents_client.messages.list(thread_id=thread.id, order=ListSortOrder.DESCENDING)
response = messages.data[0].content[0].text.value

# FunctionTool definition
from azure.ai.agents.models import FunctionTool

def my_function(param: str) -> str:
    return f"result: {param}"

tool = FunctionTool(functions=[my_function])
# Pass tool.definitions to agent creation
```

**Idempotent Create-or-Update Pattern**:
1. List agents, filter by name
2. If found: call `update_agent()` with agent_id
3. If not found: call `create_agent()`
4. Return agent object in both cases

---

## 2. Terraform — New Foundry Resource Model (azurerm >= 4.0)

**Decision**: Use `azurerm_cognitive_account` with `kind = "AIServices"` and `custom_subdomain_name` for the Foundry resource. Use `azurerm_ai_studio_project` for projects within the resource.

**Rationale**: The azurerm provider >= 4.0 maps CognitiveServices/accounts to `azurerm_cognitive_account`. Project management is enabled by default for AIServices kind — no separate flag needed. Custom subdomain is required and serves as the globally unique identifier.

**Alternatives Considered**:
- `azurerm_machine_learning_workspace` (kind=Hub/Project): Rejected — this is the classic Hub+Project model, explicitly excluded by spec FR-012.
- AzAPI provider for raw ARM: Rejected — azurerm has native support; AzAPI adds unnecessary complexity.

**Key Resources**:

```hcl
# Foundry Resource (CognitiveServices/AIServices)
resource "azurerm_cognitive_account" "foundry" {
  count               = var.use_existing_foundry ? 0 : 1
  name                = "${var.prefix}-foundry-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  kind                = "AIServices"
  sku_name            = "S0"
  custom_subdomain_name = "${var.prefix}-foundry-${var.environment}"
}

# Key Vault (always provisioned)
resource "azurerm_key_vault" "main" {
  name                = "${var.prefix}-kv-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"
  enable_rbac_authorization = true
}

# AI Search (conditional)
resource "azurerm_search_service" "main" {
  count               = var.enable_knowledge_source ? 1 : 0
  name                = "${var.prefix}-search-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "basic"
}

# RBAC role assignments
resource "azurerm_role_assignment" "rg_contributor" {
  scope                = azurerm_resource_group.main.id
  role_definition_name = "Contributor"
  principal_id         = var.ci_principal_id
}

resource "azurerm_role_assignment" "cognitive_user" {
  count                = var.use_existing_foundry ? 0 : 1
  scope                = azurerm_cognitive_account.foundry[0].id
  role_definition_name = "Cognitive Services User"
  principal_id         = var.ci_principal_id
}

resource "azurerm_role_assignment" "kv_secrets_user" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = var.ci_principal_id
}
```

**Remote State Backend**:
```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "tfstateXXXXX"
    container_name       = "tfstate"
    key                  = "foundryagent.tfstate"
  }
}
```

**Key Variables**:
- `prefix` (string): User-defined naming prefix
- `environment` (string): dev/qa/prod
- `use_existing_foundry` (bool, default: true)
- `enable_knowledge_source` (bool, default: false)
- `ci_principal_id` (string): Object ID of the CI/CD identity
- `existing_foundry_connection_string` (string, sensitive): Used when `use_existing_foundry=true`

**Outputs**:
- `project_connection_string`: From Foundry project or passed through from variable
- `resource_group_name`: Name of created RG
- `key_vault_name`: Name of created Key Vault

---

## 3. Bicep — New Foundry Resource Model

**Decision**: Use `Microsoft.CognitiveServices/accounts@2024-10-01` with `kind: 'AIServices'` for the Foundry resource. Modular structure with separate `.bicep` files for each resource type.

**Rationale**: Direct Bicep mapping of the same ARM resource types as Terraform. Module structure keeps each resource independently manageable and testable.

**Alternatives Considered**:
- Single monolithic main.bicep: Rejected — modules improve readability and reusability.
- AzD (Azure Developer CLI) templates: Rejected — too opinionated; doesn't match the project's custom structure.

**Key Modules**:

```bicep
// modules/foundry-resource.bicep
param name string
param location string
param customSubdomain string

resource foundryAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: name
  location: location
  kind: 'AIServices'
  sku: { name: 'S0' }
  properties: {
    customSubDomainName: customSubdomain
    publicNetworkAccess: 'Enabled'
  }
  identity: { type: 'SystemAssigned' }
}

output accountId string = foundryAccount.id
output endpoint string = foundryAccount.properties.endpoint
```

```bicep
// modules/keyvault.bicep
param name string
param location string
param tenantId string

resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: name
  location: location
  properties: {
    tenantId: tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
  }
}

output keyVaultName string = kv.name
output keyVaultId string = kv.id
```

**Deployment Scope**:
- Subscription-level deployment for the resource group
- Resource-group-level deployment for all other resources
- OR: Single subscription-level deployment that creates the RG then deploys modules into it

**Parameters** (bicepparam files per env):
- `prefix`: User-defined naming prefix
- `environment`: dev/qa/prod
- `useExistingFoundry`: Bool, default true
- `enableKnowledgeSource`: Bool, default false
- `ciPrincipalId`: Object ID for RBAC assignments

---

## 4. GitHub Actions OIDC — Workload Identity Federation

**Decision**: Use `azure/login@v2` with OIDC. Per-environment GitHub Environments with environment-scoped secrets. Federated credentials link each environment to its Azure AD app registration.

**Rationale**: OIDC eliminates long-lived client secrets (constitution IV.5). GitHub Environments provide natural isolation for secret scoping and approval gates.

**Alternatives Considered**:
- Client secret-based authentication: Rejected — violates constitution IV.5, FR-020.
- Single service principal for all envs: Rejected — reduces isolation; per-env SPs allow least-privilege scoping.

**Key Workflow Pattern**:

```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [main]
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

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment || 'dev' }}
    steps:
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

**Secret Naming Convention** (per GitHub Environment):
- `AZURE_CLIENT_ID` — scoped to env
- `AZURE_TENANT_ID` — scoped to env
- `AZURE_SUBSCRIPTION_ID` — scoped to env
- `FOUNDRY_PROJECT_CONNECTION_STRING` — scoped to env (used when `use_existing_foundry=true`)

**Prod Approval Gate**:
- GitHub Environment `prod` → Settings → Required reviewers → Add approvers
- Deployment branch restriction: `main` only

**Terraform OIDC**:
```yaml
      - uses: hashicorp/setup-terraform@v3
      - run: terraform init
      - run: terraform apply -auto-approve -var-file=envs/${{ inputs.environment }}.tfvars
        env:
          ARM_USE_OIDC: true
          ARM_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
          ARM_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
          ARM_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

**Bicep OIDC**:
```yaml
      - uses: azure/arm-deploy@v2
        with:
          scope: subscription
          region: ${{ vars.AZURE_REGION }}
          template: infra/bicep/main.bicep
          parameters: infra/bicep/parameters/${{ inputs.environment }}.bicepparam
```

---

## 5. pydantic-settings — Extensible Config Pattern

**Decision**: Base `FoundryBaseConfig` class using `pydantic_settings.BaseSettings` with `model_config` for env prefix and `.env` support. Each agent subclass extends the base with `AGENT_`-prefixed fields. No nested env var namespacing — flat env vars with clear naming convention.

**Rationale**: pydantic-settings v2 reads from environment variables by default, supports `.env` files via `SettingsConfigDict`, and class inheritance naturally composes shared + agent-specific settings. Flat env vars are simpler to manage in CI/CD and `.env` files than nested prefixes.

**Alternatives Considered**:
- Raw `os.environ` with manual validation: Rejected — loses type safety, validation, and default handling.
- `python-dotenv` without pydantic: Rejected — no validation, no type coercion, no defaults.
- Nested `env_prefix` per agent subclass: Rejected — overly complex for the current scale; flat vars with clear naming are simpler.

**Key Pattern**:

```python
# agents/_base/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class FoundryBaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    foundry_project_connection_string: str
    environment: str = "dev"
    azure_key_vault_name: str = ""


# agents/<agent-name>/config.py
from agents._base.config import FoundryBaseConfig

class MyAgentConfig(FoundryBaseConfig):
    agent_name: str = "my-agent"
    agent_model: str = "gpt-4o"
    agent_instructions_path: str = "agents/my-agent/instructions.md"
    knowledge_source_enabled: bool = False
    github_openapi_enabled: bool = False
    # Agent-specific
    azure_ai_search_endpoint: str = ""
    azure_ai_search_index_name: str = ""
```

**Environment Variable Mapping** (automatic by pydantic-settings):
- `FOUNDRY_PROJECT_CONNECTION_STRING` → `foundry_project_connection_string`
- `ENVIRONMENT` → `environment`
- `AGENT_NAME` → `agent_name`
- `KNOWLEDGE_SOURCE_ENABLED` → `knowledge_source_enabled`

**`.env.example`**:
```env
FOUNDRY_PROJECT_CONNECTION_STRING=<your-connection-string>
ENVIRONMENT=dev
AZURE_KEY_VAULT_NAME=myproj-kv-dev
```
