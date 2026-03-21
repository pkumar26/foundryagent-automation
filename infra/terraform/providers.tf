terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.0"
    }
  }

  # Backend configuration for Terraform remote state.
  # Values are supplied at `terraform init` time via -backend-config flags
  # (see deploy.yml) or via a backend.hcl file for local development:
  #
  #   terraform init -backend-config=backend.hcl
  #
  # Required backend-config keys:
  #   resource_group_name  — RG containing the state storage account
  #   storage_account_name — Azure Storage Account name
  #   container_name       — Blob container (default: tfstate)
  #   key                  — State file name (e.g. foundryagent-dev.tfstate)
  backend "azurerm" {}
}

provider "azurerm" {
  features {}
}
