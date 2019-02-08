#!/usr/bin/env python3

"""Run modules end to end
"""

from policy_module import PolicyModule

import sys
import argparse

def main():
    args = process_arguments()

    # Create Policy Manager Module
    policy_manager = PolicyModule(args.subscriptionid)
    policy_manager.assign(args.assignmentpath, args.scope)

def process_arguments():
    parser = argparse.ArgumentParser('deploy')
    parser.add_argument('subscriptionid', help='A subscription ID')
    parser.add_argument('assignmentpath', help='Path to Assignment')
    parser.add_argument('scope', help='Policy assignment scope')

    return parser.parse_args()

if __name__ == '__main__':
    sys.exit(main())
