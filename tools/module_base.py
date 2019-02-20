from azure.common.credentials import ServicePrincipalCredentials

try:
    from azure.cli.core._profile import Profile
except Exception:
    Profile = None

import os


class ModuleBase(object):

    ENV_TENANT_ID = 'AZURE_TENANT_ID'
    ENV_CLIENT_ID = 'AZURE_CLIENT_ID'
    ENV_CLIENT_SECRET = 'AZURE_CLIENT_SECRET'
    RESOURCE_ACTIVE_DIRECTORY = 'https://management.core.windows.net/'

    def get_credentials(self, resource=RESOURCE_ACTIVE_DIRECTORY):

        tenant_auth_variables = [
            ModuleBase.ENV_TENANT_ID, ModuleBase.ENV_CLIENT_ID,
            ModuleBase.ENV_CLIENT_SECRET
        ]

        self._is_cli_auth = False
        if all(k in os.environ for k in tenant_auth_variables):
            # Service principal authentication
            credentials = ServicePrincipalCredentials(
                client_id=os.environ[ModuleBase.ENV_CLIENT_ID],
                secret=os.environ[ModuleBase.ENV_CLIENT_SECRET],
                tenant=os.environ[ModuleBase.ENV_TENANT_ID],
                resource=resource)
        else:
            # Azure CLI authentication
            (credentials,
             subscription_id,
             tenant_id) = Profile().get_login_credentials(
                resource=resource)
            self._is_cli_auth = True

        return credentials

    def _get_access_token(self, credentials):
        if self._is_cli_auth:
            return credentials._token_retriever()[1]
        return credentials.token['access_token']
