using 'template.bicep'

var prefix = readEnvironmentVariable('RESOURCE_PREFIX')
var sanitizedPrefix = replace(prefix, '-', '')
param apiImageName = 'api'
param apiUrl = 'https://kerrokantasi-api-testi.turku.fi'
param apiWebAppName = '${prefix}-api'
param uiImageName = 'ui'
param uiUrl = 'https://kerrokantasi-testi.turku.fi'
param uiWebAppName = '${prefix}-ui'
param appInsightsName = '${prefix}-appinsights'
param cacheName = '${prefix}-cache'
param containerRegistryName = '${sanitizedPrefix}registry'
param dbName = 'kerrokantasi'
param dbServerName = '${prefix}-db'
param dbAdminUsername = 'turkuadmin'
param dbUsername = 'kerrokantasi'
param keyvaultName = '${sanitizedPrefix}kv'
param serverfarmPlanName = 'serviceplan'
param storageAccountName = '${sanitizedPrefix}st'
param apiOutboundIpName = 'turku-test-kerrokantasi-outbound-ip'
param natGatewayName = '${prefix}-nat'
param vnetName =  '${prefix}-vnet'
param workspaceName = '${prefix}-workspace'
param openIdClientId = '4b872185-8b54-4e10-b3e1-125fcd0fa0f6'
param openIdAudience = 'https://auth.turku.fi/kerrokantasi'
param openIdAuthority = 'https://testitunnistamo.turku.fi/openid'
param openIdApiTokenUrl = 'https://testitunnistamo.turku.fi/api-tokens/'
