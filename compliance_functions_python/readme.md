# Compliance Functions
This is a python function app with functions that help enforce common compliance needs.

Currently it contains the following functions:

- Ship Management Group logs to storage (periodic, 15 minutes)
- Scan for all Key Vaults and write summary to storage (periodic, daily)


## Development Environment Setup
Only docker is required for basic development and running the functions.

If you'd like to do more in-depth debugging you'll want these things:
https://docs.microsoft.com/en-us/azure/azure-functions/functions-create-first-function-python#prerequisites


## Build And Run With Docker
The easiest way to run and maintain these functions is with `docker-compose`.

First, update the environment variables in the supplied `docker-compose.yml`.

The `AzureWebJobsStorage` connection string will be used for logs and as a location to write output from the functions.

_All commands assume you are in the compliance_functions_python folder_

To ensure your containers are built fresh you can run:
```
docker-compose up --build
```

Both functions will execute immediately upon startup, then resume their normal intervals.

To install the container and leave it running permanently in the background:

```
docker-compose up -d --build
```

Or without compose:

```
docker build --rm -t compliance_functions:latest .

set AzureWebJobsStorage=DefaultEndpointsProtocol=https;AccountName=<account>;AccountKey=<key>
export AZURE_MGMT_GROUP_ID=/providers/Microsoft.Management/managementGroups/<mgmt group name>
export AZURE_CLIENT_ID=<client id>
export AZURE_TENANT_ID=<tenant id>
export AZURE_CLIENT_SECRET=<secret>
docker run -p 8080:80 -e AzureWebJobsStorage -e ManagementGroupId -e AZURE_MGMT_GROUP_ID -e AZURE_CLIENT_ID -e AZURE_TENANT_ID -e AZURE_SECRET -it compliance_functions:latest
```

Please reference the `docker-compose.yml` for available environment variables.

