import os
from module_base import ModuleBase
from azure.mgmt.resource.policy import PolicyClient

class PolicyModule(ModuleBase):

    def __init__(self, subscription_id):
        self.subscription_id = subscription_id
        self.credentials = self.get_credentials()
        self.client = PolicyClient(self.credentials, self.subscription_id)

    def deploy(self, policy_path):
        try:
            current_working_dir = os.path.abspath(os.path.dirname(__file__))
            policy_path = os.path.join(current_working_dir, policy_path)
            policy_name = os.path.splitext(os.path.basename(policy_path))[0]
            policy_definition = open(policy_path, 'r').read()
            self.client.policy_definitions.create_or_update(policy_name, policy_definition)
        except Exception as ex:
            print(ex)

    def list_policies(self):
        print('list')