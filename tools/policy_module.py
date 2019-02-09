import json
import os
import logging
from module_base import ModuleBase
from policy_logger import PolicyLoggerModule
from azure.mgmt.resource.policy import PolicyClient

class PolicyModule(ModuleBase):

    def __init__(self, subscription_id):
        self.subscription_id = subscription_id
        self.credentials = self.get_credentials()
        self.client = PolicyClient(self.credentials, self.subscription_id)
        self.logger = PolicyLoggerModule(__name__)

    def deploy(self, policy_path, management_group_id):
        try:
            policy_path = os.path.join(os.getcwd(), policy_path)
            policy_name = os.path.splitext(os.path.basename(policy_path))[0]
            policy_text = open(policy_path, 'r').read()
            policy_definition = json.loads(policy_text)

            if management_group_id is None:
                self._deploy_definition_to_subscription(policy_name, policy_definition)
            else:
                self._deploy_definition_to_management_group(policy_name, policy_definition, management_group_id)

        except Exception as ex:
            self.logger.exception_handler(ex)

    def assign(self, assignment_path, scope):
        try:
            assignment_path = os.path.join(os.getcwd(), assignment_path)
            assignment_name = os.path.splitext(os.path.basename(assignment_path))[0]
            assignment_text = open(assignment_path, 'r').read()
            assignment_definition = json.loads(assignment_text)

            self._assign_policy_to_scope(assignment_name, scope, assignment_definition)
        except Exception as ex:
            self.logger.exception_handler(ex)

    def _deploy_definition_to_subscription(self, policy_name, policy_definition):
        self.client.policy_definitions.create_or_update(policy_name, policy_definition)

    def _deploy_definition_to_management_group(self, policy_name, policy_definition, management_group_id):
        self.client.policy_definitions.create_or_update_at_management_group(policy_name, policy_definition, management_group_id)

    def _assign_policy_to_scope(self, assignment_name, scope, assignment_definition):
        self.client.policy_assignments.create(scope, assignment_name, assignment_definition)

    def list_policies(self):
        print('list')
