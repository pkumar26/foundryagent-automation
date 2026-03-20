@description('Name of the Foundry project')
param name string

@description('Azure region')
param location string

@description('Resource ID of the parent Foundry account')
param foundryAccountId string

resource existing_account 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: last(split(foundryAccountId, '/'))
}

resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2024-10-01' = {
  name: name
  location: location
  parent: existing_account
  properties: {}
}

output projectId string = foundryProject.id
