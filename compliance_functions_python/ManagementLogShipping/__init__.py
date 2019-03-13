from datetime import datetime, timedelta, timezone
import logging
import os
import requests
import json

from azure.common.credentials import UserPassCredentials, ServicePrincipalCredentials
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
            os.environ[ENV_PASSWORD]
        )
        pass

    return credentials

def get_activity_logs(group_id, start_date_delta, credentials):
    '''
    Manually call new rest endpoint to get Activity Logs for
    the Management Group scope.  It isn't in most SDKs yet.
    '''

    start_date = (datetime.utcnow() - start_date_delta).strftime("%Y-%m-%d %H:%M:%S")

    uri = ("https://management.azure.com/%s/providers/microsoft.insights/eventtypes/"
            "management/values?api-version=2017-03-01-preview&$filter=eventTimestamp ge '%s'" %
            (group_id.strip('/'), start_date))

    headers = {
        'Authorization': 'Bearer %s' % (credentials.token['access_token'])
    }

    r = requests.get(uri, headers=headers, timeout=30)

    if r.status_code != 200:
        logging.error("Log endpoint returned an error.\n%s\n%s"
                        % (r.status_code, r.text))

    return r.content


def write_events(connection_string, container_name, events):
    '''
    Try to write each event to blob storage, but if it is already
    there just ignore it.  This way we can safely process the same
    events multiple times with minimal resource expense.
    '''

    # Create the BlockBlockService that is used to call the Blob service for the storage account
    block_blob_service = BlockBlobService(connection_string=connection_string)

    # Ensure container exists
    block_blob_service.create_container(container_name)

    for event in events:
        # Build a blob path
        event_id = event['eventDataId']
        resource_id = event['resourceId'].rsplit('/', 1)[-1]
        blob_path = "%s/%s.json" % (event_id, resource_id)

        # Create if not already exists
        if not block_blob_service.exists(container_name, blob_name=blob_path):
            logging.info("Writing %s" % blob_path)
            block_blob_service.create_blob_from_text(container_name, blob_path, json.dumps(event))
        else:
            logging.info("Skipping %s" % blob_path)


def main(mytimer: func.TimerRequest) -> None:
    logging.info("Management Group Log Shipping Started.")

    # Lower logging verbosity on blob client
    logging.getLogger("azure.storage.common.storageclient").setLevel(logging.WARNING)

    group_id = os.environ['AZURE_MGMT_GROUP_ID']
    connection_string = os.environ['AzureWebJobsStorage']

    credentials = get_credentials()

    # Get the activity log data
    log_history_delta = timedelta(hours=1)
    log_data = get_activity_logs(group_id, log_history_delta, credentials)
    events = json.loads(log_data)['value']

    # Write blobs
    write_events(connection_string, "managementgroupactivity", events)

    logging.info("Management Group Log Shipping Completed.")

