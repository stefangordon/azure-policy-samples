# Deploying a Storage Account with Customer Managed Keys

Azure Storage currently needs to be created with Microsoft managed keys, then upgraded to use Customer Managed Keys.
This presents a challenge when Azure Policy is configured to deny non-compliant resources. Below is a potential workaround
that uses an excluded resource group dedicated to provisioning, and requires accounts in-provisioning to have all
network access disabled. 

1. Define the `encrypt-with-customer-keys` and `encrypt-with-customer-keys-provision` policy definitions
2. Apply the policy to your chosen scope (Management Group or Subscription) with an exclusion set for your provisioning RG
3. Create a storage acct using Microsoft keys that has all network access disabled (ex: `storage-no-cmk.json`)
4. Upgrade the storage acct to use your Customer Managed Keys (ex: `storage-cmd.json`), and set the appropriate networkAcls
5. Move the now-compliant storage acct from the provisioning RG to its final home (ex: `az resource move`)