using '../main.bicep'

param prefix = 'foundryagent'
param environment = 'dev'
param location = 'eastus'
param useExistingFoundry = true
param enableKnowledgeSource = false
param ciPrincipalId = ''
