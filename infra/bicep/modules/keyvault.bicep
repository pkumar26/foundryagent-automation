@description('Name of the Key Vault')
param name string

@description('Azure region')
param location string

@description('Azure AD tenant ID')
param tenantId string

resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: name
  location: location
  properties: {
    tenantId: tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enablePurgeProtection: true
    softDeleteRetentionInDays: 7
  }
}

output keyVaultName string = kv.name
output keyVaultId string = kv.id
