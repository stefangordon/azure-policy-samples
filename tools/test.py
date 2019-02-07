#!/usr/bin/env python3

import sys
import argparse

from functional_test_module import FunctionalTestModule


def main():
    args = process_arguments()

    tester = FunctionalTestModule(args.subscriptionid)
    tester.run(args.policydefinition)


def process_arguments():
    parser = argparse.ArgumentParser("test")
    parser.add_argument("subscriptionid", help="A subscription ID")
    parser.add_argument("policydefinition", help="Policy definition to test")
    return parser.parse_args()


if __name__ == '__main__':
    sys.exit(main())
