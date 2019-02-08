import os
import yaml


class PolicyMap(object):
    def __init__(self, config_path, definition_path, test_path):
        self.definition_path = definition_path
        self.test_path = test_path

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
        return [{'id': s['id'], 'name': s['name']} for s in self.policy_map['scopes']]

    def definitions(self, scope_id):
        definition_lists = [s['definitions'] for s in self.policy_map['scopes'] if s['id'] == scope_id]
        definitions = [os.path.join(self.definition_path, i['name'] + '.json')
                       for a in definition_lists for i in a]

        return definitions

    def assignments(self, scope_id):
        assignment_lists = [s['assignments'] for s in self.policy_map['scopes'] if s['id'] == scope_id]
        assignments = [
            {'definition': os.path.join(self.definition_path, i['name'] + '.json'),
             'parameters': i.get('parameters', {})}
            for a in assignment_lists for i in a]

        return assignments

    def tests(self):
        pass


