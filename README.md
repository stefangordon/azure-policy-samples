# Azure Policy Samples
Azure Policy samples I put together which may be useful to others.

## Force an on-demand policy evaluation
Use ARM client with the command below to scan an specific resource group.  

```
# ARMClient.exe post https://management.azure.com/subscriptions/{your sub id}/resourceGroups/{your rg}/providers/Microsoft.PolicyInsights/policyStates/latest/triggerEvaluation?api-version=2018-07-01-preview -verbose
```

You can get ARM Client at https://github.com/projectkudu/ARMClient
