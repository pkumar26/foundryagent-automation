@description('Name of the AI Search service')
param name string

@description('Azure region')
param location string

resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: name
  location: location
  sku: {
    name: 'basic'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
  }
}

output searchServiceId string = searchService.id
output searchServiceEndpoint string = 'https://${name}.search.windows.net'
