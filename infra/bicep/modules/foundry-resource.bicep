@description('Name of the Foundry resource')
param name string

@description('Azure region')
param location string

@description('Custom subdomain for the Foundry resource')
param customSubdomain string

resource foundryAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: name
  location: location
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: customSubdomain
    publicNetworkAccess: 'Enabled'
  }
  identity: {
    type: 'SystemAssigned'
  }
}

output accountId string = foundryAccount.id
output endpoint string = foundryAccount.properties.endpoint
output principalId string = foundryAccount.identity.principalId
