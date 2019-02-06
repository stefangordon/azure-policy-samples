#!/usr/bin/env python3

"""Run modules end to end
"""

from sample_module import SampleModule

import sys
import argparse


def main():
    args = process_arguments()

    # Execute Sample Module
    sample = SampleModule(args.subscriptionid, "hello world")
    sample.deploy()
    sample.test()


def process_arguments():
    parser = argparse.ArgumentParser("deploy")
    parser.add_argument("subscriptionid", help="A subscription ID")
    return parser.parse_args()


if __name__ == '__main__':
    sys.exit(main())
