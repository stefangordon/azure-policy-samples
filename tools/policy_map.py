import os
import yaml


class PolicyMap(object):
    def __init__(self, config_path, definition_path, test_path):
        self.definition_path = definition_path
        self.test_path = test_path
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
                    [os.path.join(path, f) for f in os.listdir(path) if f.endswith('.json')]

        return definition_files

    def scopes(self):
        return [s['id'] for s in self.policy_map['scopes']]

    def definitions(self, scope_id):
        definition_lists = [s['definitions'] for s in self.policy_map['scopes'] if s['id'] == scope_id and s.get('definitions') != None]
        definitions = [os.path.join(self.definition_path, i['name'] + '.json')
                       for a in definition_lists for i in a]

        return definitions

    def assignments(self, scope_id):
        assignment_lists = [s['assignments'] for s in self.policy_map['scopes'] if s['id'] == scope_id and s.get('assignments') != None]
        assignments = [
            {'definition_id': self.get_definition_id(i['name']),
             'definition_name': i['name'],
             'parameters': self._augment_parameters(i.get('parameters', {})),
             'exclusions': i.get('exclusions')}
            for a in assignment_lists for i in a]

        return assignments

    def _augment_parameters(self, parameters):
        return {k: {'value': v} for k,v in parameters.items()}

    def tests(self):
        pass

    def update_deployed(self, id, name):
        self.deployed_map[name] = id

    def get_definition_id(self, name):
        # Trim optional folder off name
        name = name.rsplit('/', 1)[-1]
        return self.deployed_map[name]

    @staticmethod
    def is_management_group(scope_id):
        return '/managementGroups' in scope_id

    @staticmethod
    def sub_id_from_scope(scope_id):
        return list(filter(None, scope_id.split('/')))[1]

    @staticmethod
    def subscription_id(scope_id):
        if not PolicyMap.is_management_group(scope_id):
            return PolicyMap.sub_id_from_scope(scope_id)
        return None

    @staticmethod
    def management_group_id(scope_id):
        if PolicyMap.is_management_group(scope_id):
            return PolicyMap.sub_id_from_scope(scope_id)
        return None

    @staticmethod
    def scope_path(scope_id):
        # Probably need to prefix something for management group here
        # This stub serves as a place for tweaks between YAML scope and
        # required SDK scope format
        return scope_id
