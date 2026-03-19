terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.0"
    }
  }

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
