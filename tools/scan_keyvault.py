#!/usr/bin/env python3

"""Run modules end to end
"""

from policy import Policy
from policy_map import PolicyMap
from azure.common.credentials import UserPassCredentials
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.keyvault import KeyVaultClient, KeyVaultAuthentication

import sys
import argparse

# For testing
from azure.cli.core._profile import Profile

def main():
    args = process_arguments()

    #credentials = UserPassCredentials(args.user, args.password)

    (credentials,
     subscription_id,
     tenant_id) = Profile().get_login_credentials()

    (credentials_keyvault,
     subscription_id,
     tenant_id) = Profile().get_login_credentials(
        resource="https://vault.azure.net")

    subscriptions = SubscriptionClient(credentials).subscriptions.list()

    for subscription in subscriptions:
        kv_client = KeyVaultManagementClient(credentials, subscription.subscription_id)
        kv_data_client = KeyVaultClient(credentials_keyvault)
        vaults = kv_client.vaults.list()

        for vault in vaults:
            print("Processing vault: %s" % vault.name)

            try:
                keys = kv_data_client.get_keys('https://' + vault.name + ".vault.azure.net/")
                for item in keys:
                    print(item)
            except:
                print("Can't access: %s" % vault.name)



def process_arguments():
    parser = argparse.ArgumentParser('deploy')
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--password', '-p', help='Password')
    return parser.parse_args()


if __name__ == '__main__':
    sys.exit(main())
