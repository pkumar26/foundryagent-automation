data "azurerm_client_config" "current" {}

# Resource Group (always provisioned)
resource "azurerm_resource_group" "main" {
  name     = "${var.prefix}-rg-${var.environment}"
  location = var.location
}

# Key Vault (always provisioned)
resource "azurerm_key_vault" "main" {
  name                       = "${var.prefix}-kv-${var.environment}"
  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  enable_rbac_authorization  = true
  purge_protection_enabled   = true
  soft_delete_retention_days = 7
}

# Foundry Resource — CognitiveServices/AIServices (conditional)
resource "azurerm_cognitive_account" "foundry" {
  count               = var.use_existing_foundry ? 0 : 1
  name                = "${var.prefix}-foundry-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  kind                = "AIServices"
  sku_name            = "S0"

  custom_subdomain_name = "${var.prefix}-foundry-${var.environment}"

  identity {
    type = "SystemAssigned"
  }
}

# Azure AI Search (conditional on knowledge source)
resource "azurerm_search_service" "main" {
  count               = var.enable_knowledge_source ? 1 : 0
  name                = "${var.prefix}-search-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "basic"
}

# RBAC Role Assignments
resource "azurerm_role_assignment" "rg_contributor" {
  count                = var.ci_principal_id != "" ? 1 : 0
  scope                = azurerm_resource_group.main.id
  role_definition_name = "Contributor"
  principal_id         = var.ci_principal_id
}

resource "azurerm_role_assignment" "cognitive_user" {
  count                = var.use_existing_foundry == false && var.ci_principal_id != "" ? 1 : 0
  scope                = azurerm_cognitive_account.foundry[0].id
  role_definition_name = "Cognitive Services User"
  principal_id         = var.ci_principal_id
}

resource "azurerm_role_assignment" "kv_secrets_user" {
  count                = var.ci_principal_id != "" ? 1 : 0
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = var.ci_principal_id
}
