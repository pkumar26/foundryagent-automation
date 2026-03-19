output "project_connection_string" {
  description = "Foundry project connection string"
  value       = var.use_existing_foundry ? var.existing_foundry_connection_string : azurerm_cognitive_account.foundry[0].endpoint
  sensitive   = true
}

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.main.name
}
