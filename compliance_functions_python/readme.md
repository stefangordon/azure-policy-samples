# Compliance Functions
This is a .net core function app with functions that help enforce common compliance needs.

Currently it contains the following functions:

- Ship Management Group logs to storage (periodic)


## Development Environment Setup
(Not required for build/run of container)

You need to install VSCode, functions extensions, C# add-ins, etc
https://docs.microsoft.com/en-us/azure/azure-functions/functions-create-first-function-vs-code#prerequisites


## Build Docker Container
If you prefer not to host in Azure Functions you can build a container for running anywhere.

The container will support MSI authentication if hosted in Azure, or you can pass service principal information
as environment variables as shown below.

The `AzureWebJobsStorage` connection string will be used for both functions logs and as a location to ship management
group logs unless you also specify `AZURE_STORAGE` to use for management group logs.

You can reference the `docker-compose.yml` as an easy way to build/run this container.

```
docker-compose up --build
```

Or build yourself:

Bash

```
docker build --rm -t compliance_functions:latest .

set AzureWebJobsStorage=DefaultEndpointsProtocol=https;AccountName=<account>;AccountKey=<key>
export AZURE_MGMT_GROUP_ID=/providers/Microsoft.Management/managementGroups/<mgmt group name>
export AZURE_CLIENT_ID=<client id>
export AZURE_TENANT_ID=<tenant id>
export AZURE_SECRET=<secret>
docker run -p 8080:80 -e AzureWebJobsStorage -e ManagementGroupId -e AZURE_MGMT_GROUP_ID -e AZURE_CLIENT_ID -e AZURE_TENANT_ID -e AZURE_SECRET -it compliance_functions:latest
```

Windows

```
docker build --rm -t compliance_functions:latest .

set AzureWebJobsStorage=DefaultEndpointsProtocol=https;AccountName=<account>;AccountKey=<key>
set AZURE_MGMT_GROUP_ID=/providers/Microsoft.Management/managementGroups/<mgmt group name>
set AZURE_CLIENT_ID=<client id>
set AZURE_TENANT_ID=<tenant id>
set AZURE_SECRET=<secret>
docker run -p 8080:80 -e AzureWebJobsStorage -e ManagementGroupId -e AZURE_MGMT_GROUP_ID -e AZURE_CLIENT_ID -e AZURE_TENANT_ID -e AZURE_SECRET -it compliance_functions:latest
```


## Local Development of Scheduled Function
You can add `, RunOnStartup=true` to the CRON metadata to make the function run as soon as you press F5.

So it would look like this:
```
    public static async Task Run([TimerTrigger("0 0 * * * *", RunOnStartup=true)]TimerInfo myTimer, ILogger log)
```

The `GetCredentials` function will also try to load a local auth file, you can go edit the path it looks at.
This is required for local dev as you won't have MSI locally.

Make this auth file in your ComplianceFunctions directory or wherever you want.  Remember you'll have to go
grant read permissions to your management group for this identity (find the identity guid in the generated file).

```
az ad sp create-for-rbac --sdk-auth > azure.auth
```


# Setting properties
When working locally set properties in the local.settings.json.

After deploying, go set these same properties as App Settings in the Function App.
