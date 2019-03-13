import datetime
import logging
import os
import json

from azure.common.credentials import UserPassCredentials, ServicePrincipalCredentials
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.keyvault import KeyVaultClient, KeyVaultAuthentication
from azure.storage.blob import BlockBlobService

import azure.functions as func

ENV_TENANT_ID = 'AZURE_TENANT_ID'
ENV_CLIENT_ID = 'AZURE_CLIENT_ID'
ENV_CLIENT_SECRET = 'AZURE_CLIENT_SECRET'
ENV_USERNAME = 'AZURE_USERNAME'
ENV_PASSWORD = 'AZURE_PASSWORD'
RESOURCE_ACTIVE_DIRECTORY = 'https://management.core.windows.net/'

def get_credentials(resource=RESOURCE_ACTIVE_DIRECTORY):
    '''
    Attempt to do either principal or credential
    authentication based on which environment variables
    we see in os.environ
    '''

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
        # Credential authentication
        credentials = UserPassCredentials(
            os.environ[ENV_USERNAME],
            os.environ[ENV_PASSWORD],
            resource=resource
        )

    return credentials

def scan_vaults(credentials, credentials_keyvault):
    # List all subscriptions we have access to
    subscriptions = SubscriptionClient(credentials).subscriptions.list()

    scan_results = {
        'vaults': []
    }

    for subscription in subscriptions:
        kv_client = KeyVaultManagementClient(credentials, subscription.subscription_id)
        kv_data_client = KeyVaultClient(credentials_keyvault)
        vaults = kv_client.vaults.list_by_subscription()

        # Loop through each vault and add it to our dictionary
        for vault in vaults:
            vault_results = {
                'vault': vault,
                'keys': []
            }

            # Try to get all the key metadata, or document if we were forbidden
            # due to a missing access policy
            try:
                keys = kv_data_client.get_keys(vault.properties.vault_uri)

                for key in keys:
                    vault_results['keys'].append(key)

                logging.info("Processed vault: %s" % vault.name)
            except:
                vault_results['keys'].append({"failed":"forbidden"})
                logging.exception("Forbidden: %s" % vault.name)
            finally:
                scan_results['vaults'].append(vault_results)

    return json.dumps(scan_results, indent=4, cls=VaultEncoder)


def write_results(connection_string, container_name, result):
    # Create the BlockBlockService that is used to call the Blob service for the storage account
    block_blob_service = BlockBlobService(connection_string=connection_string)

    # Ensure container exists
    block_blob_service.create_container(container_name)

    # Build a blob path
    date_string = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    blob_path = "%s.json" % date_string

    # Write
    logging.info("Writing %s" % blob_path)
    block_blob_service.create_blob_from_text(container_name, blob_path, result)


def main(mytimer: func.TimerRequest) -> None:
    logging.info('Key Vault scan function started.')

    # We need credentials for two different resource URIs
    credentials = get_credentials()
    credentials_keyvault = get_credentials(resource="https://vault.azure.net")
    connection_string = os.environ['AzureWebJobsStorage']

    # Scan vaults
    result = scan_vaults(credentials, credentials_keyvault)

    # Store result
    write_results(connection_string, "keyvaultscans", result)

    logging.info('Key Vault scan function completed.')


class VaultEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, '__dict__'):
            return o.__dict__
        return None

