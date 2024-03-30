# filevault
This is an encrypted vault to stash away files. Written python, it uses 7z to compress and encrypts files using a unique key for each file.  If you don't want to back up your data on the cloud, this could be a solution for you. Please give it a try

## Tools and frameworks used

   * sqllite3 database (included in python)
   * 7z

## Usage


### Getting Started

   * Add 7z to your system path
   * Start the file vault using the command `python3 filevault.py`. This should start the shell with a prompt `vault>`

### Creating a Vault

To create a vault use the command `create`. The example below creates a vault called `tmp7` and stores the encryption key in a file called `key7`. The vault is created int he vaults directory while the key file is stored in the current working directory

```
vault>create vaults/tmp8 key8
Created table vault_registry
created table vault_config
vault created at vaults/tmp8. Please open the vault with the key file key8
!!!WARNING!!! -> Pleae store the key key8 in a secure place
vault>

```
*Please make sure you store the key generated in a secure location. Please do not store it in the vault itself or even on the same device as the vault*

### Listing the contents of the vault


