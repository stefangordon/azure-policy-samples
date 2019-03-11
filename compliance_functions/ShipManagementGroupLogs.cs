using System;
using System.Linq;
using System.Threading.Tasks;
using System.Net.Http;
using System.IO;

using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Host;
using Microsoft.WindowsAzure.Storage.Blob;
using Microsoft.WindowsAzure.Storage;
using Microsoft.Azure.Management.Fluent;
using Microsoft.Azure.Management.ResourceManager.Fluent;
using Microsoft.Azure.Management.ResourceManager.Fluent.Core;
using Microsoft.Azure.Management.ResourceManager.Fluent.Authentication;
using Microsoft.Extensions.Logging;

using Newtonsoft.Json;
using Newtonsoft.Json.Linq;


namespace Microsoft.Sample
{
    // The function will poll and write Management Group activity logs to storage.
    // It will not write duplicates, so just set the LOG_AGE to something larger than
    // the expected function run interval.  Some overlap will ensure no logs are lost if the
    // function executes late.
    // Example below shows function running hourly with a LOG_AGE of 2 hours.
    public static class ShipManagementGroupLogs
    {
        private static readonly string GROUP_ENV = "AZURE_MGMT_GROUP_ID";
        private static readonly string MSI_ENDPOINT = "MSI_ENDPOINT";
        private static readonly string STORAGE_ENV = "AZURE_STORAGE";
        private static readonly string WEBJOB_ENV = "AzureWebJobsStorage";
        private static readonly string CLIENT_ENV = "AZURE_CLIENT_ID";
        private static readonly string TENANT_ENV = "AZURE_TENANT_ID";
        private static readonly string SECRET_ENV = "AZURE_SECRET";
        private static readonly string USER_ENV = "AZURE_USERNAME";
        private static readonly string PASSWORD_ENV = "AZURE_PASSWORD";
        private static readonly string STORAGE_CONTAINER = "managementgrouplogs";

        private static readonly TimeSpan LOG_AGE = TimeSpan.FromHours(2);


        [FunctionName("ShipManagementGroupLogs")]
        public static async Task Run([TimerTrigger("0 0 * * * *", RunOnStartup=true)]TimerInfo myTimer, ILogger log, ExecutionContext context)
        {
            // These variables come from the Application Settings configured in the portal at runtime
            // or from local.settings.json during local testing
            // or from environment variables passed in to `docker run`
            var groupId = Environment.GetEnvironmentVariable(GROUP_ENV);
            var storageConnectionString = Environment.GetEnvironmentVariable(STORAGE_ENV);

            if (string.IsNullOrWhiteSpace(storageConnectionString))
            {
                storageConnectionString = Environment.GetEnvironmentVariable(WEBJOB_ENV);
            }

            log.LogInformation($"Management Group Log Shipping Running at: {DateTime.Now} for {groupId}");

            AzureCredentials credentials = GetCredentials(log, context);

            // Download the activity logs
            var logs = await GetActivityLog(groupId, credentials, log);

            // Parse and write them to storage
            await WriteLogsToStorage(logs, storageConnectionString, log);
        }

        private static AzureCredentials GetCredentials(ILogger log, ExecutionContext context)
        {
            // MSI authentication is used in Azure, or a fallback to a credentials file for local dev

            if (!String.IsNullOrEmpty(Environment.GetEnvironmentVariable(MSI_ENDPOINT)))
            {
                var msiInformation = new MSILoginInformation(MSIResourceType.AppService);
                return (new AzureCredentialsFactory()).FromMSI(msiInformation, AzureEnvironment.AzureGlobalCloud);
            }
            else if(!string.IsNullOrEmpty(Environment.GetEnvironmentVariable(SECRET_ENV)))
            {
                return SdkContext.AzureCredentialsFactory.FromServicePrincipal(
                    Environment.GetEnvironmentVariable(CLIENT_ENV),
                    Environment.GetEnvironmentVariable(SECRET_ENV),
                    Environment.GetEnvironmentVariable(TENANT_ENV),
                    AzureEnvironment.AzureGlobalCloud
                );
            }
            else if(!string.IsNullOrEmpty(Environment.GetEnvironmentVariable(USER_ENV)))
            {
                log.LogCritical("Not Yet Implemented");
                return null;
            }
            else
            {
                var functionRootPath = Directory.GetParent(context.FunctionDirectory).FullName;
                var credFilePath = Path.Combine(functionRootPath, "bin", "azure.auth");
                log.LogCritical("MSI Authentication is not enabled.  Trying a credentials file at: " + credFilePath);

                // You can create an auth file like this:
                // az ad sp create-for-rbac --sdk-auth > azure.auth
                // You can update this path as appropriate in your debugging scenario.
                return SdkContext.AzureCredentialsFactory.FromFile(credFilePath);
            }
        }

        private static async Task WriteLogsToStorage(string logs, string storageConnectionString, ILogger log)
        {
            // Connect to storage account
            var storageAccount = CloudStorageAccount.Parse(storageConnectionString);
            var cloudBlobClient = storageAccount.CreateCloudBlobClient();

            // Ensure storage container exists
            var cloudBlobContainer = cloudBlobClient.GetContainerReference(STORAGE_CONTAINER);
            await cloudBlobContainer.CreateIfNotExistsAsync();

            // Parse the logs JSON
            var parsedLogs = JObject.Parse(logs);

            foreach (var logEvent in parsedLogs["value"])
            {
                // Extract some key values to identify this log event
                var eventDataId = (string)logEvent["eventDataId"];
                var resourceId = (string)logEvent["resourceId"];

                // These should never be null
                if (string.IsNullOrWhiteSpace(eventDataId) || string.IsNullOrWhiteSpace(resourceId))
                {
                    log.LogError("Unable to parse activity log due to null identifiers.");
                }

                // Generate a blob path of resourceid/eventid.json
                var blobPath = String.Format("{0}/{1}.json", resourceId.Split("/").Last(), eventDataId);

                // Write the blob if it doesn't already exist
                log.LogInformation("Writing event " + blobPath);
                CloudBlockBlob cloudBlockBlob = cloudBlobContainer.GetBlockBlobReference(blobPath);
                if (!await cloudBlockBlob.ExistsAsync())
                {
                    await cloudBlockBlob.UploadTextAsync(logEvent.ToString());
                }
            }
        }

        private static async Task<string> GetActivityLog(string groupId, AzureCredentials credentials, ILogger log)
        {
            // Create a New HttpClient object and dispose it when done, so the app doesn't leak resources
            using (HttpClient client = new HttpClient())
            {
                // Call asynchronous network methods in a try/catch block to handle exceptions
                try
                {
                    var startDate = DateTime.UtcNow.Subtract(LOG_AGE).ToString("O");

                    var uri = string.Format("https://management.azure.com/{0}/providers/microsoft.insights/eventtypes/" +
                    "management/values?api-version=2017-03-01-preview&%24filter=eventTimestamp%20ge%20'{1}'",
                    groupId.Trim('/'),
                    startDate);

                    var request = new HttpRequestMessage(HttpMethod.Get, uri);

                    System.Threading.CancellationTokenSource cts = new System.Threading.CancellationTokenSource();
                    System.Threading.CancellationToken token = cts.Token;
                    await credentials.ProcessHttpRequestAsync(request, token);

                    HttpResponseMessage response = await client.SendAsync(request);
                    response.EnsureSuccessStatusCode();
                    string responseBody = await response.Content.ReadAsStringAsync();
                    return responseBody;
                }
                catch (HttpRequestException e)
                {
                    log.LogCritical("Message :{0} ", e.Message);
                    return e.Message;
                }
            }
        }
    }
}
