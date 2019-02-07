import json
import os
from module_base import ModuleBase
from azure.mgmt.resource.policy import PolicyClient

class PolicyModule(ModuleBase):

    def __init__(self, subscription_id):
        self.subscription_id = subscription_id
        self.credentials = self.get_credentials()
        self.client = PolicyClient(self.credentials, self.subscription_id)

    def deploy(self, policy_path, management_group_id):
        try:
            policy_path = os.path.join(os.getcwd(), policy_path)
            policy_name = os.path.splitext(os.path.basename(policy_path))[0]
            policy_text = open(policy_path, 'r').read()
            policy_definition = json.loads(policy_text)

            if management_group_id is None:
                self.__deploy_definition_to_subscription(policy_name, policy_definition)
            else:
                self.__deploy_definition_to_management_group(policy_name, policy_definition, management_group_id)

        except Exception as ex:
            print(ex)

    def __deploy_definition_to_subscription(self, policy_name, policy_definition):
        self.client.policy_definitions.create_or_update(policy_name, policy_definition)

    def __deploy_definition_to_management_group(self, policy_name, policy_definition, management_group_id):
        self.client.policy_definitions.create_or_update_at_management_group(policy_name, policy_definition, management_group_id)

    def list_policies(self):
        print('list')
