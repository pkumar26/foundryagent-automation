# Infrastructure Deployment Guide

[![Terraform >= 1.5](https://img.shields.io/badge/Terraform-%3E%3D1.5-7B42BC?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![Bicep](https://img.shields.io/badge/Bicep-IaC-0078D4?logo=microsoftazure&logoColor=white)](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
[![Azure CLI](https://img.shields.io/badge/Azure%20CLI-2.x-0078D4?logo=microsoftazure&logoColor=white)](https://learn.microsoft.com/en-us/cli/azure/)
[![Azure Key Vault](https://img.shields.io/badge/Key%20Vault-RBAC-0078D4?logo=microsoftazure&logoColor=white)](https://learn.microsoft.com/en-us/azure/key-vault/)

This guide covers how to provision and manage the Azure infrastructure for the Foundry Agent Platform using either **Terraform** or **Bicep**. Both tools produce identical environments.

---

## Table of Contents

- [What Gets Deployed](#what-gets-deployed)
- [Prerequisites](#prerequisites)
- [Choose Your IaC Tool](#choose-your-iac-tool)
- [Option A: Terraform](#option-a-terraform)
  - [1. Setup Remote State Backend](#1-setup-remote-state-backend)
  - [2. Initialize Terraform](#2-initialize-terraform)
  - [3. Configure Variables](#3-configure-variables)
  - [4. Plan and Apply](#4-plan-and-apply)
  - [5. Retrieve Outputs](#5-retrieve-outputs)
  - [6. Destroy Infrastructure](#6-destroy-infrastructure)
- [Option B: Bicep](#option-b-bicep)
  - [1. Deploy with Azure CLI](#1-deploy-with-azure-cli)
  - [2. Configure Parameters](#2-configure-parameters)
  - [3. Run the Deployment](#3-run-the-deployment)
  - [4. Retrieve Outputs](#4-retrieve-outputs-1)
  - [5. Tear Down](#5-tear-down)
- [Parameter Reference](#parameter-reference)
- [Resource Architecture](#resource-architecture)
- [Environment Configuration](#environment-configuration)
- [RBAC Roles](#rbac-roles)
- [CI/CD Integration](#cicd-integration)
- [Common Scenarios](#common-scenarios)
- [Troubleshooting](#troubleshooting)

---

## What Gets Deployed

| Resource | Always | Conditional |
|----------|--------|-------------|
| Resource Group | Yes | — |
| Key Vault (RBAC-enabled, purge-protected) | Yes | — |
| Foundry Resource (CognitiveServices/AIServices) | — | `use_existing_foundry = false` |
| Foundry Project | — | `use_existing_foundry = false` (Bicep only) |
| Azure AI Search (Basic tier) | — | `enable_knowledge_source = true` |
| RBAC: Contributor on Resource Group | — | `ci_principal_id` is set |
| RBAC: Key Vault Secrets User | — | `ci_principal_id` is set |
| RBAC: Cognitive Services User on Foundry | — | `ci_principal_id` is set AND `use_existing_foundry = false` |

---

## Prerequisites

- **Azure CLI** >= 2.x — [Install](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
- **Azure subscription** with permissions to create resources
- Authenticated session: `az login`
- **For Terraform:** Terraform >= 1.5 — [Install](https://developer.hashicorp.com/terraform/install)
- **For Bicep:** Azure CLI includes Bicep (verify with `az bicep version`; upgrade with `az bicep upgrade`)

---

## Choose Your IaC Tool

| Consideration | Terraform | Bicep |
|---------------|-----------|-------|
| Multi-cloud support | Yes | Azure only |
| State management | Remote backend required | No state file |
| Learning curve | HCL syntax | ARM-like syntax |
| Destroy support | `terraform destroy` | Manual or `az group delete` |
| CI/CD integration | Both supported via `deploy.yml` | Both supported via `deploy.yml` |

Both tools deploy identical resources. Pick whichever your team is comfortable with.

---

## Option A: Terraform

All Terraform files are in `infra/terraform/`.

### 1. Setup Remote State Backend

Terraform requires a remote backend for state. Create an Azure Storage Account for state storage (one-time setup):

```bash
# Set variables
STATE_RG="tfstate-rg"
STATE_SA="tfstatefoundryagent"    # must be globally unique
STATE_CONTAINER="tfstate"
LOCATION="eastus"

# Create the state resources
az group create --name "$STATE_RG" --location "$LOCATION"
az storage account create \
  --name "$STATE_SA" \
  --resource-group "$STATE_RG" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --allow-blob-public-access false
az storage container create \
  --name "$STATE_CONTAINER" \
  --account-name "$STATE_SA"
```

### 2. Initialize Terraform

```bash
cd infra/terraform

terraform init \
  -backend-config="resource_group_name=$STATE_RG" \
  -backend-config="storage_account_name=$STATE_SA" \
  -backend-config="container_name=$STATE_CONTAINER" \
  -backend-config="key=foundryagent-dev.tfstate"
```

**Tip:** For convenience, create a `backend.hcl` file (do **not** commit it):

```hcl
# infra/terraform/backend.hcl  (git-ignored)
resource_group_name  = "tfstate-rg"
storage_account_name = "tfstatefoundryagent"
container_name       = "tfstate"
key                  = "foundryagent-dev.tfstate"
```

Then init with:

```bash
terraform init -backend-config=backend.hcl
```

### 3. Configure Variables

Environment-specific variable files live in `infra/terraform/envs/`:

```
infra/terraform/envs/
├── dev.tfvars
├── qa.tfvars
└── prod.tfvars
```

Example `dev.tfvars`:

```hcl
prefix                  = "foundryagent"
environment             = "dev"
location                = "eastus"
use_existing_foundry    = true
enable_knowledge_source = false
ci_principal_id         = ""
```

Edit the appropriate `.tfvars` file for your environment. Key decisions:

- **`use_existing_foundry = true`** (default): Skip Foundry resource creation — you already have a Foundry project and endpoint URL.
- **`use_existing_foundry = false`**: Provision a new CognitiveServices/AIServices resource and generate an endpoint URL.
- **`enable_knowledge_source = true`**: Provision an Azure AI Search service for RAG/knowledge source scenarios.
- **`ci_principal_id`**: Set this to the Object ID of your CI/CD service principal to assign RBAC roles automatically.

### 4. Plan and Apply

```bash
# Preview changes
terraform plan -var-file=envs/dev.tfvars

# Apply (creates resources)
terraform apply -var-file=envs/dev.tfvars
```

For non-interactive CI pipelines, add `-auto-approve`:

```bash
terraform apply -var-file=envs/dev.tfvars -auto-approve
```

### 5. Retrieve Outputs

After a successful apply:

```bash
# Resource group name
terraform output resource_group_name

# Key Vault name
terraform output key_vault_name

# Foundry project endpoint (sensitive — only shown explicitly)
terraform output -raw project_endpoint
```

Use the endpoint in your `.env`:

```bash
echo "AZURE_AI_PROJECT_ENDPOINT=$(terraform output -raw project_endpoint)" >> ../../.env
```

### 6. Destroy Infrastructure

```bash
terraform destroy -var-file=envs/dev.tfvars
```

---

## Option B: Bicep

All Bicep files are in `infra/bicep/`.

### 1. Deploy with Azure CLI

Bicep deployments are triggered via `az deployment group create` (resource-group-scoped). The resource group must already exist.

### 2. Configure Parameters

Environment-specific parameter files live in `infra/bicep/parameters/`:

```
infra/bicep/parameters/
├── dev.bicepparam
├── qa.bicepparam
└── prod.bicepparam
```

Example `dev.bicepparam`:

```bicepparam
using '../main.bicep'

param prefix = 'foundryagent'
param environment = 'dev'
param location = 'eastus'
param useExistingFoundry = true
param enableKnowledgeSource = false
param ciPrincipalId = ''
```

Edit the parameter file matching your target environment. See [Parameter Reference](#parameter-reference) for full details.

### 3. Run the Deployment

```bash
cd infra/bicep

# Deploy to dev
az deployment sub create \
  --location eastus \
  --template-file main.bicep \
  --parameters parameters/dev.bicepparam \
  --name "foundryagent-dev-$(date +%s)"

# Deploy to qa
az deployment sub create \
  --location eastus \
  --template-file main.bicep \
  --parameters parameters/qa.bicepparam \
  --name "foundryagent-qa-$(date +%s)"

# Deploy to prod
az deployment sub create \
  --location eastus \
  --template-file main.bicep \
  --parameters parameters/prod.bicepparam \
  --name "foundryagent-prod-$(date +%s)"
```

> **Note:** The `--location` flag sets where the _deployment metadata_ is stored, not where resources are created. Resource location is controlled by the `location` parameter inside the `.bicepparam` file.

### 4. Retrieve Outputs

```bash
# Get all outputs from the deployment
az deployment sub show \
  --name "<deployment-name>" \
  --query "properties.outputs"

# Get specific outputs
az deployment sub show \
  --name "<deployment-name>" \
  --query "properties.outputs.resourceGroupName.value" -o tsv

az deployment sub show \
  --name "<deployment-name>" \
  --query "properties.outputs.keyVaultName.value" -o tsv

az deployment sub show \
  --name "<deployment-name>" \
  --query "properties.outputs.projectConnectionString.value" -o tsv
```

### 5. Tear Down

Bicep has no built-in destroy command. Delete the resource group:

```bash
az group delete --name foundryagent-rg-dev --yes --no-wait
```

---

## Parameter Reference

| Parameter | Terraform Variable | Bicep Parameter | Type | Default | Description |
|-----------|--------------------|-----------------|------|---------|-------------|
| Naming prefix | `prefix` | `prefix` | string | — | Prefix for all resource names (e.g., `foundryagent`) |
| Environment | `environment` | `environment` | string | — | `dev`, `qa`, or `prod` |
| Region | `location` | `location` | string | `eastus` | Azure region for all resources |
| Use existing Foundry | `use_existing_foundry` | `useExistingFoundry` | bool | `true` | Skip Foundry provisioning if you already have a project |
| Enable AI Search | `enable_knowledge_source` | `enableKnowledgeSource` | bool | `false` | Provision Azure AI Search for knowledge source |
| CI/CD principal | `ci_principal_id` | `ciPrincipalId` | string | `""` | Object ID of CI/CD identity for RBAC assignments |
| Existing endpoint | `existing_foundry_endpoint` | _N/A_ | string | `""` | (Terraform only) Endpoint URL when using existing Foundry |

---

## Resource Architecture

```
<prefix>-rg-<env>                          (Resource Group)
├── <prefix>-kv-<env>                      (Key Vault — RBAC, purge-protected)
├── <prefix>-foundry-<env>                 (CognitiveServices/AIServices — conditional)
│   └── <prefix>-project-<env>             (Foundry Project — conditional, Bicep only)
└── <prefix>-search-<env>                  (AI Search — conditional)
```

### Naming Convention

All resources follow the pattern: `<prefix>-<resource-type>-<environment>`

For example, with `prefix=foundryagent` and `environment=dev`:
- Resource Group: `foundryagent-rg-dev`
- Key Vault: `foundryagent-kv-dev`
- Foundry: `foundryagent-foundry-dev`
- AI Search: `foundryagent-search-dev`

---

## Environment Configuration

Three environments are pre-configured with parameter files:

| Environment | Terraform | Bicep | Typical Use |
|-------------|-----------|-------|-------------|
| **dev** | `envs/dev.tfvars` | `parameters/dev.bicepparam` | Local development, feature branches |
| **qa** | `envs/qa.tfvars` | `parameters/qa.bicepparam` | Integration testing, staging |
| **prod** | `envs/prod.tfvars` | `parameters/prod.bicepparam` | Production workloads |

All environments default to:
- `location = eastus`
- `use_existing_foundry = true` (BYO Foundry project)
- `enable_knowledge_source = false` (no AI Search)
- `ci_principal_id = ""` (no RBAC assignments)

Customise these per environment before deploying.

---

## RBAC Roles

When `ci_principal_id` is provided, the following roles are assigned to the CI/CD service principal:

| Role | Scope | Purpose |
|------|-------|---------|
| **Contributor** | Resource Group | Manage all resources within the group |
| **Key Vault Secrets User** | Key Vault | Read secrets during deployments |
| **Cognitive Services User** | Foundry Resource | Access Foundry APIs (only if `use_existing_foundry = false`) |

To find your service principal's Object ID:

```bash
# For an app registration
az ad sp show --id <app-id> --query id -o tsv

# For the currently logged-in user
az ad signed-in-user show --query id -o tsv
```

---

## CI/CD Integration

The `deploy.yml` GitHub Actions workflow automates infrastructure provisioning and agent deployment.

### Workflow Dispatch Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `environment` | yes | — | `dev`, `qa`, or `prod` |
| `infra_tool` | yes | `terraform` | `terraform` or `bicep` |
| `use_existing_foundry` | yes | `true` | Use existing Foundry or provision new |
| `agent_target` | yes | `all` | Deploy `all` agents or a specific agent name |

### Authentication

The workflow uses **OIDC with Workload Identity Federation** — no client secrets required. Set up these GitHub secrets:

| Secret | Description |
|--------|-------------|
| `AZURE_CLIENT_ID` | App registration Client ID |
| `AZURE_TENANT_ID` | Azure AD Tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Target subscription ID |
| `AZURE_AI_PROJECT_ENDPOINT` | Azure AI project endpoint URL (when using existing project) |

For Terraform remote state, also set:

| Secret | Description |
|--------|-------------|
| `TF_STATE_RESOURCE_GROUP` | Resource group for state storage |
| `TF_STATE_STORAGE_ACCOUNT` | Storage account name |
| `TF_STATE_CONTAINER` | Blob container name |

### Trigger Behavior

| Environment | Trigger |
|-------------|---------|
| **dev** | Automatic on push to `main` |
| **qa** / **prod** | Manual dispatch only |

---

## Common Scenarios

### Scenario 1: Use an Existing Foundry Project (Default)

You already have an Azure AI Foundry project and endpoint URL. Infrastructure only creates the resource group and Key Vault.

```bash
# Terraform
terraform apply -var-file=envs/dev.tfvars
# use_existing_foundry is already true in dev.tfvars

# Then configure your .env
echo "AZURE_AI_PROJECT_ENDPOINT=<your-project-endpoint>" >> .env
```

### Scenario 2: Provision a New Foundry Project

Set `use_existing_foundry = false` in your parameter file, then deploy. The endpoint URL will be available in the outputs.

```bash
# Terraform
sed -i 's/use_existing_foundry.*=.*/use_existing_foundry = false/' envs/dev.tfvars
terraform apply -var-file=envs/dev.tfvars

# Grab the endpoint
terraform output -raw project_endpoint
```

```bash
# Bicep — edit parameters/dev.bicepparam, set useExistingFoundry = false, then:
az deployment sub create \
  --location eastus \
  --template-file main.bicep \
  --parameters parameters/dev.bicepparam \
  --name "foundryagent-dev-$(date +%s)"
```

### Scenario 3: Enable AI Search for Knowledge Sources

Set `enable_knowledge_source = true` to provision an Azure AI Search service (Basic tier).

```bash
# Terraform
sed -i 's/enable_knowledge_source.*=.*/enable_knowledge_source = true/' envs/dev.tfvars
terraform apply -var-file=envs/dev.tfvars
```

### Scenario 4: Set Up CI/CD RBAC

Find your service principal's Object ID and set `ci_principal_id`:

```bash
SP_OBJECT_ID=$(az ad sp show --id <app-id> --query id -o tsv)

# Terraform
sed -i "s/ci_principal_id.*=.*/ci_principal_id = \"$SP_OBJECT_ID\"/" envs/dev.tfvars
terraform apply -var-file=envs/dev.tfvars
```

### Scenario 5: Deploy to Multiple Environments

```bash
# Dev
terraform init -backend-config=backend.hcl  # key=foundryagent-dev.tfstate
terraform apply -var-file=envs/dev.tfvars

# QA (re-init with different state key)
terraform init -backend-config=backend.hcl -backend-config="key=foundryagent-qa.tfstate" -reconfigure
terraform apply -var-file=envs/qa.tfvars

# Prod
terraform init -backend-config=backend.hcl -backend-config="key=foundryagent-prod.tfstate" -reconfigure
terraform apply -var-file=envs/prod.tfvars
```

---

## Troubleshooting

### Terraform init fails with backend errors

Ensure the storage account, container, and resource group exist. Double-check the backend config values.

```bash
az storage account show --name <storage-account-name> --query "id" -o tsv
az storage container show --name tfstate --account-name <storage-account-name>
```

### Key Vault name already taken

Key Vault names are globally unique. If you get a conflict, change the `prefix` to something unique.

### Bicep deployment fails with authorization error

The Bicep template deploys at resource group scope. Ensure the resource group exists and your service principal has Contributor access at the resource group level. Use `az deployment group create` with `--resource-group <name>`.

### Terraform state lock errors

If a previous run was interrupted, the state may be locked:

```bash
terraform force-unlock <lock-id>
```

### Resource group deletion hangs

Key Vault has purge protection enabled with a 7-day retention. If you need to recreate resources with the same name, purge the soft-deleted vault first:

```bash
az keyvault purge --name <vault-name>
```

### RBAC assignments fail

Ensure the `ci_principal_id` is the **Object ID** (not the Application/Client ID) of the service principal:

```bash
# Correct: Object ID
az ad sp show --id <app-id> --query id -o tsv

# Wrong: Application ID (this won't work for RBAC)
az ad sp show --id <app-id> --query appId -o tsv
```
