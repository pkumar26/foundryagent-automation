using '../main.bicep'

param prefix = 'foundryagent'
param environment = 'qa'
param location = 'eastus'
param useExistingFoundry = true
param enableKnowledgeSource = false
param ciPrincipalId = ''
