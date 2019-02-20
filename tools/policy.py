import json
import os
import requests

from azure.mgmt.resource.policy import PolicyClient
from resource_util import ResourceUtil

from logger import PolicyLogger
from module_base import ModuleBase


class Policy(ModuleBase):

    def __init__(self, subscription_id, management_group_id):
        self.credentials = self.get_credentials()
        self.client = None
        self.subscription_id = subscription_id
        self.management_group_id = management_group_id
        self.logger = PolicyLogger(__name__)

        # SDK incorrectly requires subscription ID to have a value
        if management_group_id:
            self.client = PolicyClient(self.credentials, "not applicable")
        else:
            self.client = PolicyClient(self.credentials, self.subscription_id)

    def list(self):
        if self.management_group_id is None:
            definitions = self.client.policy_definitions.list()
        else:
            definitions = self.client.policy_definitions.list_by_management_group(
                self.management_group_id)

        return [{'id': d['id'], 'name': d['name']} for d in definitions]

    def deploy(self, policy_path):
        try:
            policy_text = open(policy_path, 'r').read()
            policy_name = os.path.splitext(os.path.basename(policy_path))[0]
            policy_definition = json.loads(policy_text)

            if self.management_group_id is None:
                result = self.client.policy_definitions.create_or_update(policy_name,
                                                                         policy_definition)
            else:
                result = self.client.policy_definitions.create_or_update_at_management_group(policy_name,
                                                                                             policy_definition,
                                                                                             self.management_group_id)
            return {'id': result.id, 'name': result.name}

        except Exception as ex:
            self.logger.exception_handler(ex)

    def assign(self, scope, definition_name, definition_id, parameters):
        try:
            name = "Assignment for " + definition_name
            assignment = {
                "displayName": name,
                "metadata": {
                    "assignedBy": "policy tool"
                },
                "parameters": parameters,
                "policyDefinitionId": definition_id,
                "scope": scope
            }
            self._assign_policy_to_scope(scope, name, assignment)
            self.client.policy_assignments.get()
        except Exception as ex:
            self.logger.exception_handler(ex)

    def _assign_policy_to_scope(self, scope, assignment_name, assignment_definition):
        self.client.policy_assignments.create(
            scope, assignment_name, assignment_definition)

    def list_assignments(self, scope):
        token = self._get_access_token(self.credentials)
        headers = {'Authorization': 'Bearer {}'.format(token)}
        url = 'https://management.azure.com{}/providers/Microsoft.Authorization/policyAssignments?api-version=2018-03-01&$filter=atScope()'.format(
            scope)
        r = requests.get(url, headers=headers)
        assignments = r.json()['value']
        return assignments

    def get(self, definition_id):
        parts = definition_id.split('/')
        name = parts[-1]
        if '/managementgroups/' in definition_id.lower():
            mg = parts[4]
            return self.client.policy_definitions.get_at_management_group(name, mg)
        else:
            subscription_id = parts[2]
            client = PolicyClient(self.credentials, subscription_id)
            return client.policy_definitions.get(name)

    def list_definitions(self, scope_id):
        if ResourceUtil.is_management_group(scope_id):
            mg = ResourceUtil.management_group_id(scope_id)
            return list(self.client.policy_definitions.list_by_management_group(mg))
        else:
            subscription_id = ResourceUtil.subscription_id(scope_id)
            client = PolicyClient(self.credentials, subscription_id)
            return list(client.policy_definitions.list(filter='atScope()'))
