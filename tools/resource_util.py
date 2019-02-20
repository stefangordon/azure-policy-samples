class ResourceUtil(object):

    @staticmethod
    def policy_definition_id(scope_id, name):
        return '{}/providers/Microsoft.Authorization/policyDefinitions/{}'.format(scope_id, name)

    @staticmethod
    def is_management_group(scope_id):
        return '/managementgroups' in scope_id.lower()

    # TODO: move this to regex or whatever
    # TODO: check to make sure scope isn't a subscription/rg/resource
    @staticmethod
    def management_group_id(scope_id):
        parts = scope_id.split('/')
        return parts[4]

    # TODO: move this to regex or whatever
    # TODO: check to make sure scope isn't a management group
    @staticmethod
    def subscription_id(scope_id):
        parts = scope_id.split('/')
        return parts[2]
