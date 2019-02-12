import json
import logging
import os
import time
from enum import Enum

from azure.mgmt.resource.policy import PolicyClient
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode
from msrestazure.azure_exceptions import CloudError, CloudErrorData
from requests.exceptions import HTTPError

from policy import Policy
from module_base import ModuleBase

# Policy Assignments aren't immediately effective
# This determines how long to wait after assignment before proceeding with further steps
WAIT_TIME_SECONDS = 5

logger = logging.getLogger(__name__)


class DeploymentResult(Enum):
    Success = 0
    DeploymentFailure = 1


class FunctionalTest(ModuleBase):

    def __init__(self, subscription_id):
        self.subscription_id = subscription_id
        self.credentials = self.get_credentials()
        self.client = ResourceManagementClient(
            self.credentials, self.subscription_id)
        self.policy = Policy(self.subscription_id, None)

    def get_definition_name(self, policy_path):
        return os.path.basename(policy_path)[:-5]

    def setup(self, resource_group, policy_path):
        logger.info('Creating resource group: %s', resource_group)
        self.client.resource_groups.create_or_update(
            resource_group, {'location': 'westus2'})
        self.policy.deploy(policy_path)
        self._create_policy_assignment(resource_group, policy_path)

    # Manually create a policy assignment without a JSON file
    # TODO: refactor Policy to support this
    def _create_policy_assignment(self, resource_group, policy_path):
        logger.info('Creating policy assignment: %s', policy_path)

        rg = self.client.resource_groups.get(resource_group)
        hack_policy = PolicyClient(self.credentials, self.subscription_id)
        definition_id = self.get_policy_definition_id(policy_path)
        definition_name = self.get_definition_name(policy_path)
        assignment_name = definition_name
        hack_policy.policy_assignments.create(
            rg.id, assignment_name, {'properties': {'scope': rg.id, 'policyDefinitionId': definition_id}})

        # Policy Assignments aren't immediately effective - wait for them to take effect
        time.sleep(WAIT_TIME_SECONDS)

    def get_policy_definition_id(self, policy_path):
        hack_policy = PolicyClient(self.credentials, self.subscription_id)
        definition_name = self.get_definition_name(policy_path)
        return hack_policy.policy_definitions.get(definition_name).id

    def teardown(self, resource_group):
        logger.info('Deleting resource group: %s', resource_group)
        self.client.resource_groups.delete(resource_group)

    def deploy_template(self, resource_group, template_path):
        template_name = os.path.basename(template_path)
        logger.info('Deploying template: %s', template_name)
        try:
            with open(template_path, 'r') as f:
                template = json.load(f)

            properties = {
                'mode': DeploymentMode.incremental,
                'template': template
            }
            deployment = self.client.deployments.create_or_update(
                resource_group, template_name, properties)
            deployment.wait()
            logger.info('Deployment success: %s', template_path)
            return DeploymentResult.Success, None
        except Exception as ex:
            logger.info('Deployment failure: %s', template_path)
            return DeploymentResult.DeploymentFailure, ex

    def is_failed_due_to_policy(self, ex, policy_definition_id):
        if not isinstance(ex, CloudError):
            return False

        # This works for the trivial case but may fail if there are additional 'details' or 'additionalInfo' elements
        if isinstance(ex.error, HTTPError):
            text = ex.error.response.text
            err = json.loads(text)['error']

            return (err['code'] == 'InvalidTemplateDeployment'
                    and err['details'][0]['code'] == 'RequestDisallowedByPolicy'
                    and err['details'][0]['additionalInfo'][0]['type'] == 'PolicyViolation'
                    and err['details'][0]['additionalInfo'][0]['info']['policyDefinitionId'] == policy_definition_id)
        elif isinstance(ex.error, CloudErrorData):
            message = ex.error.details[0].message
            if isinstance(message, str):
                message = json.loads(message)

            return (ex.error.error == 'DeploymentFailed'
                    and message['error']['code'] == 'RequestDisallowedByPolicy'
                    and message['error']['additionalInfo'][0]['type'] == 'PolicyViolation'
                    and message['error']['additionalInfo'][0]['info']['policyDefinitionId'] == policy_definition_id)

        raise Exception('Inconclusive result') from ex

    def run(self, policy, resource_group, arm_template, expected_result):
        try:
            self.setup(resource_group, policy)
            actual_result, ex = self.deploy_template(
                resource_group, arm_template)

            if expected_result == 'success':
                assert actual_result == DeploymentResult.Success, 'Template should deploy successfully: {}'.format(
                    arm_template)
            elif expected_result == 'blockedByPolicy':
                policy_definition_id = self.get_policy_definition_id(policy)
                rejected = self.is_failed_due_to_policy(
                    ex, policy_definition_id)
                assert rejected == True, 'Deployment should fail due to policy: {}'.format(
                    arm_template)

            logger.info("Test succeeded")
        finally:
            self.teardown(resource_group)

    @staticmethod
    def discover_policies(definitions):
        # Recursively discover all policies
        policies = []
        for dirpath, _, files in os.walk(definitions):
            for f in files:
                if 'tests' in dirpath:
                    continue

                rel_dir = os.path.relpath(dirpath, definitions)
                relative_path = os.path.join(rel_dir, f)
                policies.append(relative_path)
        return policies

    @staticmethod
    def discover_tests(definitions, policy_path):
        # expected policy_path: ['Microsoft.Storage', 'deny-unrestricted-access.json']

        # By convention, look into the 'tests/*' directory
        parts = os.path.normpath(policy_path).split(os.path.sep)
        parts.insert(0, 'tests')
        parts[-1] = parts[-1][:-5]
        search_root = os.path.join(definitions, *parts)

        # Recursively discover all positive/negative tests
        tests = []
        for dirpath, _, files in os.walk(search_root):
            for f in files:
                abs_path = os.path.join(os.path.abspath(dirpath), f)
                if f.startswith('pass'):
                    tests.append((abs_path, 'success'))
                elif f.startswith('fail'):
                    tests.append((abs_path, 'blockedByPolicy'))
                else:
                    logger.debug('Skipped file: %s', f)

        # warn if there are no tests for a given policy definition
        if not tests:
            logger.warning('No test cases found for %s', policy_path)

        return tests
