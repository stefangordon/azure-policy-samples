#!/usr/bin/env python3

from functional_test import FunctionalTest
import argparse
import logging
import sys


def main():
    _setup_logger()
    args = _process_arguments()

    policy = args.policydefinition
    resource_group = args.resourcegroup
    arm_template = args.armtemplate
    expected_result = args.expectedresult

    tester = FunctionalTest(args.subscriptionid)
    tester.run(policy, resource_group, arm_template, expected_result)


def _process_arguments():
    parser = argparse.ArgumentParser("test")
    parser.add_argument("--subscriptionid",
                        help="A subscription ID", required=True)
    parser.add_argument("--resourcegroup",
                        help="A resource group", required=True)
    parser.add_argument("--policydefinition",
                        help="Policy definition to test", required=True)
    parser.add_argument(
        "--armtemplate", help="An ARM template used to validate the policy", required=True)
    parser.add_argument(
        "--expectedresult", help="The expected result [success,blockedByPolicy]", required=True)
    return parser.parse_args()


def _setup_logger():
    # create logger
    logger = logging.getLogger('functional_test')
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)


if __name__ == '__main__':
    sys.exit(main())
