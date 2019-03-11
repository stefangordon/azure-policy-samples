from datetime import datetime, timedelta, timezone
import logging
import os
import requests

from azure.common.credentials import UserPassCredentials, ServicePrincipalCredentials
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.keyvault import KeyVaultClient, KeyVaultAuthentication

import azure.functions as func

ENV_TENANT_ID = 'AZURE_TENANT_ID'
ENV_CLIENT_ID = 'AZURE_CLIENT_ID'
ENV_CLIENT_SECRET = 'AZURE_CLIENT_SECRET'
RESOURCE_ACTIVE_DIRECTORY = 'https://management.core.windows.net/'

def get_credentials(resource=RESOURCE_ACTIVE_DIRECTORY):
    tenant_auth_variables = [
        ENV_TENANT_ID, ENV_CLIENT_ID,
        ENV_CLIENT_SECRET
    ]

    if all(k in os.environ for k in tenant_auth_variables):
        # Service principal authentication
        credentials = ServicePrincipalCredentials(
            client_id=os.environ[ENV_CLIENT_ID],
            secret=os.environ[ENV_CLIENT_SECRET],
            tenant=os.environ[ENV_TENANT_ID],
            resource=resource)
    else:
        # Azure CLI authentication
        pass

    return credentials

def get_activity_logs(group_id, credentials):
    #var startDate = DateTime.UtcNow.Subtract(LOG_AGE).ToString("O");

    start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")

    uri = ("https://management.azure.com/%s/providers/microsoft.insights/eventtypes/"
            "management/values?api-version=2017-03-01-preview&$filter=eventTimestamp ge '%s'" %
            (group_id.strip('/'), start_date))

    headers = {
        'Authorization': 'Bearer %s' % (credentials.token['access_token'])
    }

    r = requests.get(uri, headers=headers, timeout=30)

    if r.status_code != 200:
        self.log.error("Application service returned an error.\n%s\n%s"
                        % (r.status_code, r.text))

    return r.content


def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.utcnow().replace(
        tzinfo=timezone.utc).isoformat()

    logging.info("Management Log Shipping started...")
    group_id = os.environ['AZURE_MGMT_GROUP_ID']
    credentials = get_credentials()
    logging.info(get_activity_logs(group_id, credentials))

