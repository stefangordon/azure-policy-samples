import json
import os

from enum import Enum
from module_base import ModuleBase
from policy_module import PolicyModule
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode
from msrestazure.azure_exceptions import CloudError


class DeploymentResult(Enum):
    Success = 0
    DeploymentFailure = 1


class FunctionalTestModule(ModuleBase):

    def __init__(self, subscription_id):
        self.subscription_id = subscription_id
        self.credentials = self.get_credentials()
        self.client = ResourceManagementClient(self.credentials, self.subscription_id)
        self.policy = PolicyModule(self.subscription_id)

    def run(self, policy_path):
        # example policy_path: 'definitions/Microsoft.Storage/deny-unrestricted-access.json'
        policy_definition_name = os.path.basename(policy_path)[:-5]
        
        # Create a RG w/ policy definition & assignments
        resource_group = policy_definition_name
        self._setup(resource_group, policy_path)
        policy_definition_id = '/subscriptions/{}/providers/Microsoft.Authorization/policyDefinitions/{}'.format(self.subscription_id, policy_definition_name)

        # Create deployments to exercise policies
        positive_tests, negative_tests = self._discover_tests(policy_path)
        self._run_negative_tests(resource_group, negative_tests, policy_definition_id)
        self._run_positive_tests(resource_group, positive_tests)

        # Teardown RG
        self._teardown(resource_group)
        # TODO: Delete policy definition


    def _setup(self, resource_group, policy_path):
        print('Creating resource group: ', resource_group)
        self.client.resource_groups.create_or_update(resource_group, {'location': 'westus2'})
        self.policy.deploy(policy_path, None)
        # TODO: Create a policy assignment


    def _discover_tests(self, policy_path):
        # expected: ['definitions', 'Microsoft.Storage', 'deny-unrestricted-access.json']

        # By convention, look into the 'definitions/tests/*' directory
        parts = os.path.normpath(policy_path).split(os.path.sep)
        parts.insert(1, 'tests')
        parts[-1] = parts[-1][:-5]
        search_root = os.path.join(os.getcwd(), *parts)

        # Recursively discover all positive/negative tests
        positive_tests = []
        negative_tests = []
        for dirpath, _, files in os.walk(search_root):
            for f in files:
                abs_path = os.path.join(os.path.abspath(dirpath), f)
                if f.startswith('pass'):
                    positive_tests.append(abs_path)
                elif f.startswith('fail'):
                    negative_tests.append(abs_path)
                else:
                    print('Skipped file: ', f)

        if not positive_tests and not negative_tests:
            print('No test cases found for ', policy_path)

        return positive_tests, negative_tests


    def _teardown(self, resource_group):
        print('Deleting resource group: ', resource_group)
        self.client.resource_groups.delete(resource_group)


    def _run_negative_tests(self, resource_group, negative_tests, policy_definition_id):
        for template_path in negative_tests:
            template_name = os.path.basename(template_path)
            print('Running tests for template: ', template_name)

            result, ex = self._deploy_template(resource_group, template_path)
            if result == DeploymentResult.Success:
                print('Error: Non-compliant template was successfully deployed')
            else:
                if self._is_failed_due_to_policy(ex, policy_definition_id):
                    print('Pass: Bad template blocked by policy definition: ', policy_definition_id)
                else:
                    print('Error: Deployment failed with error: ', ex)


    def _run_positive_tests(self, resource_group, positive_tests):
        for template_path in positive_tests:
            template_name = os.path.basename(template_path)
            print('Running tests for template: ', template_name)

            result, ex = self._deploy_template(resource_group, template_path)
            if result == DeploymentResult.Success:
                print('Pass: Template successfully deployed')
            else:
                print('Error: Deployment failed with error: ', ex)


    def _deploy_template(self, resource_group, template_path):
        template_name = os.path.basename(template_path)
        print('Deploying template: ', template_name)
        try:
            with open(template_path, 'r') as f:
                template = json.load(f)

            properties = {
                'mode': DeploymentMode.incremental,
                'template': template
            }
            deployment = self.client.deployments.create_or_update(resource_group, template_name, properties)
            deployment.wait()
            return DeploymentResult.Success, None
        except Exception as ex:
            return DeploymentResult.DeploymentFailure, ex


    def _is_failed_due_to_policy(self, ex, policy_definition_id):
        if type(ex) is not CloudError:
            return False
        
        text = ex.error.response.text
        err = json.loads(text)['error']

        # This works for the trivial case but may fail if there are additional 'details' or 'additionalInfo' elements
        return (err['code'] == 'InvalidTemplateDeployment' 
            and err['details'][0]['code'] == 'RequestDisallowedByPolicy' 
            and err['details'][0]['additionalInfo'][0]['type'] == 'PolicyViolation'
            and err['details'][0]['additionalInfo'][0]['info']['policyDefinitionId'] == policy_definition_id)
