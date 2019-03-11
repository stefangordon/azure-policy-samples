import datetime
import logging
import os

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

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)

    #credentials = UserPassCredentials(args.user, args.password)

    credentials = get_credentials()
    credentials_keyvault = get_credentials(resource="https://vault.azure.net")

    subscriptions = SubscriptionClient(credentials).subscriptions.list()

    for subscription in subscriptions:
        kv_client = KeyVaultManagementClient(credentials, subscription.subscription_id)
        kv_data_client = KeyVaultClient(credentials_keyvault)
        vaults = kv_client.vaults.list()

        for vault in vaults:
            print("Processing vault: %s" % vault.name)

            try:
                keys = kv_data_client.get_keys('https://' + vault.name + ".vault.azure.net/")
                for item in keys:
                    print(item)
            except:
                print("Can't access: %s" % vault.name)




