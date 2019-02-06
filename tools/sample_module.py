from module_base import ModuleBase
from azure.mgmt.resource.policy import PolicyClient


class SampleModule(ModuleBase):

    def __init__(self, subscription_id, parameter2):
        self.subscription_id = subscription_id
        self.parameter2 = parameter2

    def deploy(self):
        client = PolicyClient(self.get_credentials(), self.subscription_id)
        print(client.policy_assignments.list())


    def test(self):
        print("Test")
