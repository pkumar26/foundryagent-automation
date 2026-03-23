targetScope = 'subscription'

@description('Naming prefix for all resources')
param prefix string

@description('Deployment environment (dev, qa, prod)')
@allowed(['dev', 'qa', 'prod'])
param environment string

@description('Azure region for all resources')
param location string = 'eastus'

@description('Whether to use an existing Foundry project')
param useExistingFoundry bool = true

@description('Whether to provision Azure AI Search')
param enableKnowledgeSource bool = false

@description('Object ID of the CI/CD identity for RBAC assignments')
param ciPrincipalId string = ''

// Resource Group
resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: '${prefix}-rg-${environment}'
  location: location
}

// Key Vault
module keyVault 'modules/keyvault.bicep' = {
  name: 'deploy-keyvault'
  scope: rg
  params: {
    name: '${prefix}-kv-${environment}'
    location: location
    tenantId: tenant().tenantId
  }
}

// Foundry Resource (conditional)
module foundryResource 'modules/foundry-resource.bicep' = if (!useExistingFoundry) {
  name: 'deploy-foundry-resource'
  scope: rg
  params: {
    name: '${prefix}-foundry-${environment}'
    location: location
    customSubdomain: '${prefix}-foundry-${environment}'
  }
}

// Foundry Project (conditional)
module foundryProject 'modules/foundry-project.bicep' = if (!useExistingFoundry) {
  name: 'deploy-foundry-project'
  scope: rg
  params: {
    name: '${prefix}-project-${environment}'
    location: location
    foundryAccountId: useExistingFoundry ? '' : foundryResource.outputs.accountId
  }
  dependsOn: [
    foundryResource
  ]
}

// AI Search (conditional)
module aiSearch 'modules/ai-search.bicep' = if (enableKnowledgeSource) {
  name: 'deploy-ai-search'
  scope: rg
  params: {
    name: '${prefix}-search-${environment}'
    location: location
  }
}

// RBAC Role Assignments
module rbacContributor 'modules/rbac-contributor.bicep' = if (ciPrincipalId != '') {
  name: 'deploy-rbac-contributor'
  scope: rg
  params: {
    principalId: ciPrincipalId
    resourceGroupId: rg.id
  }
}

module rbacKvUser 'modules/rbac-kv-user.bicep' = if (ciPrincipalId != '') {
  name: 'deploy-rbac-kv-user'
  scope: rg
  params: {
    principalId: ciPrincipalId
    keyVaultName: keyVault.outputs.keyVaultName
  }
}

module rbacCognitiveUser 'modules/rbac-cognitive-user.bicep' = if (!useExistingFoundry && ciPrincipalId != '') {
  name: 'deploy-rbac-cognitive-user'
  scope: rg
  params: {
    principalId: ciPrincipalId
    foundryAccountName: '${prefix}-foundry-${environment}'
  }
  dependsOn: [
    foundryResource
  ]
}

// Outputs
output resourceGroupName string = rg.name
output keyVaultName string = keyVault.outputs.keyVaultName
// Note: camelCase to match Bicep conventions. Deploy workflow maps this to AZURE_AI_PROJECT_ENDPOINT.
output projectEndpoint string = useExistingFoundry ? '' : foundryResource.outputs.endpoint
