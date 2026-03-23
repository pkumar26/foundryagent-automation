@description('Naming prefix for all resources')
param prefix string

@description('Deployment environment (dev, qa, prod)')
@allowed(['dev', 'qa', 'prod'])
param environment string

@description('Azure region for all resources')
param location string = 'eastus2'

@description('Whether to use an existing Foundry project')
param useExistingFoundry bool = true

@description('Whether to provision Azure AI Search')
param enableKnowledgeSource bool = false

@description('Object ID of the CI/CD identity for RBAC assignments')
param ciPrincipalId string = ''

// Key Vault
module keyVault 'modules/keyvault.bicep' = {
  name: 'deploy-keyvault'
  params: {
    name: '${prefix}-kv-${environment}'
    location: location
    tenantId: tenant().tenantId
  }
}

// Foundry Resource (conditional)
module foundryResource 'modules/foundry-resource.bicep' = if (!useExistingFoundry) {
  name: 'deploy-foundry-resource'
  params: {
    name: '${prefix}-foundry-${environment}'
    location: location
    customSubdomain: '${prefix}-foundry-${environment}'
  }
}

// Foundry Project (conditional)
module foundryProject 'modules/foundry-project.bicep' = if (!useExistingFoundry) {
  name: 'deploy-foundry-project'
  params: {
    name: '${prefix}-project-${environment}'
    location: location
    #disable-next-line BCP318
    foundryAccountId: foundryResource.outputs.accountId
  }
}

// AI Search (conditional)
module aiSearch 'modules/ai-search.bicep' = if (enableKnowledgeSource) {
  name: 'deploy-ai-search'
  params: {
    name: '${prefix}-search-${environment}'
    location: location
  }
}

// RBAC Role Assignments
module rbacContributor 'modules/rbac-contributor.bicep' = if (ciPrincipalId != '') {
  name: 'deploy-rbac-contributor'
  params: {
    principalId: ciPrincipalId
    resourceGroupId: resourceGroup().id
  }
}

module rbacKvUser 'modules/rbac-kv-user.bicep' = if (ciPrincipalId != '') {
  name: 'deploy-rbac-kv-user'
  params: {
    principalId: ciPrincipalId
    keyVaultName: keyVault.outputs.keyVaultName
  }
}

module rbacCognitiveUser 'modules/rbac-cognitive-user.bicep' = if (!useExistingFoundry && ciPrincipalId != '') {
  name: 'deploy-rbac-cognitive-user'
  params: {
    principalId: ciPrincipalId
    foundryAccountName: '${prefix}-foundry-${environment}'
  }
}

// Outputs
output keyVaultName string = keyVault.outputs.keyVaultName
// Note: camelCase to match Bicep conventions. Deploy workflow maps this to AZURE_AI_PROJECT_ENDPOINT.
#disable-next-line BCP318
output projectEndpoint string = !useExistingFoundry ? foundryResource.outputs.endpoint : ''
