import json
import os
import yaml

from azure.mgmt.resource.policy.models import PolicyDefinition

from resource_util import ResourceUtil
from policy import Policy
from policy_map import PolicyMap
from module_base import ModuleBase


class PolicyDiff(ModuleBase):

    def __init__(self, subscription_id, map_path, definition_path):
        self.subscription_id = subscription_id
        self.policy = Policy(self.subscription_id, None)
        self.policy_map = PolicyMap(map_path, definition_path)
        self.definition_path = definition_path

    def diff(self):
        for scope in self.policy_map.scopes():
            scope_id = PolicyMap.scope_id(scope)

            expected_assignments = scope['assignments']
            expected_definitions = self.policy_map.definitions(scope)

            actual_assignments = self.policy.list_assignments(scope_id)
            actual_definitions = self.policy.list_definitions(scope_id)
            self._compare_definitions(
                expected_definitions, actual_definitions, scope_id)
            self._compare_assignments(expected_assignments, actual_assignments)

    def _get_assignments(self, scope_id):
        return

    def _compare_definitions(self, expected_definitions, actual_definitions, scope_id):
        print('\nScope: ', scope_id)

        # todo: replace everything below with a proper diff algorithm
        # todo: compare expected vs actual definitions
        for d in expected_definitions:
            expected_name = d.name
            actual = [act for act in actual_definitions if act.display_name ==
                      expected_name and scope_id in act.id]

            if len(actual) > 1:
                print(
                    "Multiple policies with same display name found: {}".format(actual))
                continue

            if len(actual) == 0:
                print('No deployed policy definition found for:', expected_name)
                continue

            a = actual[0]
            if (d.mode.lower() == a.mode.lower()
                and d.parameters == a.parameters
                    and d.policy_rule == a.policy_rule):
                print('OK: ', expected_name)
            else:
                print("Expected does not match actual")
                print('\nExpected: ', d)
                print('\nActual:', actual[0])

    def _compare_assignments(self, expected_assignments, actual_assignments):
        pass
