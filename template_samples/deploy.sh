#!/bin/bash

read -p 'Resource Group: ' rgName
echo $rgName

read -p 'Location (default: Central US): ' resourceLocation
echo "${resourceLocation:=Central US}"

read -p 'Storage Name: ' storageName
echo $storageName

read -p 'Key Vault Name: ' vaultname
read -p 'Key Name: ' keyname
read -p 'Key Version: ' version

echo Verifying Resource Group
az group create --name $rgName --location "$resourceLocation"

echo Deploying Storage Account and Creating Access Policy
az group deployment create --resource-group $rgName --template-file storage_step1.json --parameters storageAccountName=$storageName \
keyvaultname=$vaultname


echo Configuring Storage Account Encryption
az group deployment create --resource-group $rgName --template-file storage_step2.json --parameters storageAccountName=$storageName \
keyvaultname=$vaultname keyname=$keyname keyversion=$version

