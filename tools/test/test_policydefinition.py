from tools.functional_test import FunctionalTest, DeploymentResult
from random import randint


def test_policydefinition(subscription_id, policy, arm_template, expected_result):
    t = FunctionalTest(subscription_id)
    resource_group = '{}-{}'.format(t.get_definition_name(policy),
                                    randint(0, 10000))
    t.run(policy, resource_group, arm_template, expected_result)
