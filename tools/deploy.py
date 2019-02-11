#!/usr/bin/env python3

"""Run modules end to end
"""

from policy import Policy
from policy_map import PolicyMap

import sys
import argparse


def main():
    args = process_arguments()

    policy_map = PolicyMap(args.map_path, args.definition_path, args.test_path)

    # Iterate over scopes to deploy
    for scope in policy_map.scopes():
        print("Deploying definitions for scope: %s" % scope)

        # Definitions required for this scope
        for definition in policy_map.definitions(scope):
            print("Processing Definition: %s" % definition)
            policy = Policy(PolicyMap.subscription_id(scope), PolicyMap.management_group_id(scope))
            policy_map.update_deployed(**policy.deploy(definition))

    # Iterate over scopes to assign
    for scope in policy_map.scopes():
        print("Deploying assignments for scope: %s" % scope)

        # Assignments required for this scope
        for assignment in policy_map.assignments(scope):
            print("Processing Assignment %s with parameters %s" %
                  (assignment['definition_name'], assignment['parameters']))
            policy = Policy(PolicyMap.subscription_id(scope), PolicyMap.management_group_id(scope))
            policy.assign(scope, **assignment)


def process_arguments():
    parser = argparse.ArgumentParser('deploy')
    parser.add_argument('--definition-path', '-d', help='Path to Azure Policy Definitions folder')
    parser.add_argument('--test-path', '-t', help='Path to Tests folder')
    parser.add_argument('--map-path', '-m', help='Path to policy map YAML', default=None)
    return parser.parse_args()


if __name__ == '__main__':
    sys.exit(main())
