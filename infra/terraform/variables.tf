variable "prefix" {
  description = "Naming prefix for all resources (e.g., 'myproj')"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, qa, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "qa", "prod"], var.environment)
    error_message = "Environment must be one of: dev, qa, prod."
  }
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "eastus"
}

variable "use_existing_foundry" {
  description = "Whether to use an existing Foundry project (true) or create a new one (false)"
  type        = bool
  default     = true
}

variable "enable_knowledge_source" {
  description = "Whether to provision Azure AI Search for knowledge source integration"
  type        = bool
  default     = false
}

variable "ci_principal_id" {
  description = "Object ID of the CI/CD identity for RBAC role assignments"
  type        = string
  default     = ""
}

variable "existing_foundry_endpoint" {
  description = "Foundry project endpoint URL when using an existing project"
  type        = string
  default     = ""
  sensitive   = true
}
