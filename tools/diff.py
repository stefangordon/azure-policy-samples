#!/usr/bin/env python3

import argparse
import sys

from policy_diff import PolicyDiff


def main():
    args = process_arguments()
    diff = PolicyDiff(args.subscription_id,
                      args.map_path,
                      args.definition_path)
    diff.diff()


def process_arguments():
    parser = argparse.ArgumentParser('diff')
    parser.add_argument('--subscription-id', '-s', help='A subscription ID')
    parser.add_argument('--map-path', '-m',
                        help='Path to policy map YAML', required=True)
    parser.add_argument('--definition-path', '-d',
                        help='Path to Azure Policy Definitions folder', default='definitions')
    return parser.parse_args()


if __name__ == '__main__':
    sys.exit(main())
