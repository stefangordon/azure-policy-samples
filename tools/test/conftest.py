import logging
import os
import pytest

from functional_test import FunctionalTest

logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption('--subscription_id', required=True,
                     help='The id of an Azure Subscription to run tests in')
    parser.addoption('--definitions', default='../../definitions',
                     help='The policy definitions path')
    parser.addoption('--policy',
                     help='A specific policy definition to test. Ex: \'Microsoft.Storage/deny-unrestricted-access.json\'')


def pytest_generate_tests(metafunc):
    if metafunc.definition.name == 'test_policydefinition':
        subscription_id = _get_arg(metafunc, 'subscription_id')
        policy = _get_arg(metafunc, 'policy')
        definitions = _get_arg(metafunc, 'definitions')

        policies = FunctionalTest.discover_policies(definitions)
        if policy:
            policies = [p for p in policies if p == policy]

        test_cases = []
        for p in policies:
            tests = [(subscription_id, p, t[0], t[1])
                     for t in FunctionalTest.discover_tests(definitions, p)]
            test_cases += tests
        metafunc.parametrize(
            'subscription_id,policy,arm_template,expected_result', test_cases)


def _get_arg(metafunc, name):
    arg = metafunc.config.getoption(name)
    if arg:
        return arg.strip('"\'')
    return None
