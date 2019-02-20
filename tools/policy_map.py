import json
import os
import yaml

from resource_util import ResourceUtil
from azure.mgmt.resource.policy.models import PolicyDefinition


class PolicyMap(object):
    def __init__(self, config_path, definition_path):
        self.definition_path = definition_path
        self.deployed_map = {}

        with open(config_path) as f:
            self.policy_map = yaml.safe_load(f)

    def definition_files(self):
        namespace_folders = os.listdir(self.definition_path)
        definition_files = list()

        for folder in namespace_folders:
            path = os.path.join(self.definition_path, folder)
            if os.path.isdir(path):
                definition_files += \
                    [os.path.join(path, f)
                     for f in os.listdir(path) if f.endswith('.json')]

        return definition_files

    def scopes(self):
        return self.policy_map['scopes']

    def scope_ids(self):
        return [s['id'] for s in self.policy_map['scopes']]

    def definition_paths(self, scope_id):
        definition_lists = [s['definitions']
                            for s in self.policy_map['scopes'] if s['id'] == scope_id]
        definitions = [os.path.join(self.definition_path, i['name'] + '.json')
                       for a in definition_lists for i in a]

        return definitions

    def definitions(self, scope):
        scope_id = PolicyMap.scope_id(scope)
        return [self._get_definition(self.definition_path, a, scope_id)
                for a in scope.get('definitions', [])]

    def assignments(self, scope_id):
        assignment_lists = [s['assignments']
                            for s in self.policy_map['scopes'] if s['id'] == scope_id]
        assignments = [
            {'definition_id': self.get_definition_id(i['name']),
             'definition_name': i['name'],
             'parameters': i.get('parameters', {})}
            for a in assignment_lists for i in a]

        return assignments

    def update_deployed(self, id, name):
        self.deployed_map[name] = id

    def get_definition_id(self, name):
        # Trim optional folder off name
        name = name.rsplit('/', 1)[-1]
        return self.deployed_map[name]

    def _get_definition(self, definition_path, policy, scope_id):
        display_name = PolicyMap.policy_name(policy)
        policy_path = os.path.join(
            definition_path, PolicyMap.policy_path(policy))
        with open(policy_path) as f:
            def_dict = json.load(f)
            def_dict['id'] = ResourceUtil.policy_definition_id(
                scope_id, display_name)
            def_dict['name'] = display_name
            definition = PolicyDefinition.from_dict(def_dict)
            return definition

    @staticmethod
    def sub_id_from_scope(scope_id):
        return list(filter(None, scope_id.split('/')))[1]

    @staticmethod
    def subscription_id(scope_id):
        if not ResourceUtil.is_management_group(scope_id):
            return PolicyMap.sub_id_from_scope(scope_id)
        return None

    @staticmethod
    def management_group_id(scope_id):
        if ResourceUtil.is_management_group(scope_id):
            return PolicyMap.sub_id_from_scope(scope_id)
        return None

    @staticmethod
    def scope_id(scope):
        if '/managementgroups' in scope['id'].lower():
            return '/providers/Microsoft.Management{}'.format(scope['id'])
        return scope['id']

    @staticmethod
    def scope_path(scope_id):
        # Probably need to prefix something for management group here
        # This stub serves as a place for tweaks between YAML scope and
        # required SDK scope format
        return scope_id

    @staticmethod
    def policy_name(policy):
        # Convert 'Microsoft.Storage/require-secure-transfer'
        # To 'require-secure-transfer'
        return policy['name'].split('/')[-1]

    @staticmethod
    def policy_path(policy):
        # Convert 'Microsoft.Storage/require-secure-transfer'
        # To 'Microsoft.Storage/require-secure-transfer.json'
        return '{}.json'.format(policy['name'])
