# Azure Policy Samples
Azure Policy samples I put together which may be useful to others.

## For defining a policy in a subscription

```
# ARMClient.exe PUT "/subscriptions/{subscriptionId}/providers/Microsoft.Authorization/policyDefinitions/AuditStorageAccounts?api-version=2016-12-01" @<path to policy definition JSON file>
```

## For defining a policy in a management group

```
# ARMClient.exe PUT "/providers/Microsoft.Management/managementgroups/{managementGroupId}/providers/Microsoft.Authorization/policyDefinitions/AuditStorageAccounts?api-version=2016-12-01" @<path to policy definition JSON file>
```

## Force an on-demand policy evaluation
Use ARM client with the command below to scan an specific resource group.  

```
# ARMClient.exe post https://management.azure.com/subscriptions/{your sub id}/resourceGroups/{your rg}/providers/Microsoft.PolicyInsights/policyStates/latest/triggerEvaluation?api-version=2018-07-01-preview -verbose
```

You can get ARM Client at https://github.com/projectkudu/ARMClient
