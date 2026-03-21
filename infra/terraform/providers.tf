terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.0"
    }
  }

  # Backend configuration for Terraform remote state.
  # Before running `terraform init`, update these values:
  #   1. Create an Azure Storage Account for state (or use an existing one)
  #   2. Create a blob container named "tfstate" in that account
  #   3. Replace "tfstateXXXXX" below with your storage account name
  #   4. Update resource_group_name to match the RG containing the storage account
  # For local development, you can remove the backend block entirely to use local state.
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "tfstateXXXXX"
    container_name       = "tfstate"
    key                  = "foundryagent.tfstate"
  }
}

provider "azurerm" {
  features {}
}
