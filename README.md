# filevault
This is an encrypted vault to stash away files. Written python, it uses 7z to compress and encrypts files using a unique key for each file.  If you don't want to back up your data on the cloud, this could be a solution for you. Please give it a try

## Tools and frameworks used

   * sqllite3 database (included in python)
   * 7z

## Usage


### Getting Started

   * Add 7z to your system path
   * Start the file vault using the command `python3 filevault.py`. This should start the shell with a prompt `vault>`
   * To end a session type `exit` which will close any open vaults and end the interactive prompt

### Creating a Vault

To create a vault use the `create` command. The example below creates a vault called `tmp7` and stores the encryption key in a file called `key7`. The vault is created int he vaults directory while the key file is stored in the current working directory

```
vault>create vaults/tmp8 key8
Created table vault_registry
created table vault_config
vault created at vaults/tmp8. Please open the vault with the key file key8
!!!WARNING!!! -> Pleae store the key key8 in a secure place
vault>

```
*Please make sure you store the key generated in a secure location. Please do not store it in the vault itself or even on the same device as the vault*

### Openning a Vault


Use the `open` command to open a vault. The commands needs the path to the vault and the key used to decrypt the vault's database. The example below opens a vault that is located in `vaults/tmp8` using the key in the file `key8`

```
vault>open vaults/tmp8 key8
vault vaults/tmp8 opened
vault>
```


### Stashing files into the Vault

Use the `stash` command to encrypt and store a file into the vault. The file will be erased from the source location permanently. In the example below, the file in the path `test/test.txt` is stashed away in the vault that is currently open (`vaults/tmp8`). The output of the stash command gives you information on the storage of the file in the vault.

```
vault>open vaults/tmp8 key8
vault vaults/tmp8 opened
vault>stash test/test.txt

id         : 1
file       : test.txt
file path  : test
vault path : vaults/tmp8/00000/256.7z
timestamp  : 2024-03-30 11:44:50.404053
vault>
```

### Stashing a directory into the Vault

Use the `stash_directory` command to stash all files in the directory into the vault. This is not a recursive command. It will only stash the files found in the directory

```
vault>stash_directory test/etc

id         : 3
file       : mtab
file path  : test/etc
vault path : vaults/tmp8/00000/153.7z
timestamp  : 2024-03-30 21:50:42.351686
vault>
```

### Listing the contents of the Vault

Use the `list` command to list the contents of the vault. The command takes an optional argument which is used to filter the listing to match the word. 

The example below lists all the contents of the vault that is open

```
vault>list
Number of files in the vault: 2
id   |  file name| path|               vault path|time added
-----------------------------------------------------------------------------------------------------------------
    1|   test.txt| test| vaults/tmp8/00000/256.7z| 2024-03-30 11:44:50
    2| letter.txt| test|  vaults/tmp8/00000/95.7z| 2024-03-30 11:48:44
vault>
```

The examle below lists the contents that match the word test in the vault that is open

```
vault>list test
Number of files in the vault: 2
id   | file name| path|               vault path|time added
-----------------------------------------------------------------------------------------------------------------
    1| test.txt| test| vaults/tmp8/00000/256.7z| 2024-03-30 11:44:50
vault>
```

### Retrieving a file from the Vault

Use the `retrieve` command using the id of the file in the vault to recreate the file in the original location.  The file is (re)created in the location where it was stashed from. If a relative path was used in teh stash command, the file is recreated relative to the current working directory. In the example below, the vault `id=1` is retrieved which corresponds to `test.txt` . The file is recreated in the path `test/`

```
vault>list test
Number of files in the vault: 2
id   | file name| path|               vault path|time added
-----------------------------------------------------------------------------------------------------------------
    1| test.txt| test| vaults/tmp8/00000/256.7z| 2024-03-30 11:44:50
vault>retrieve 1
vault>
```


### Viewing information on a vault entry

Use the `info` command to view the information on any file. See example below

```
vault>list
Number of files in the vault: 3
id   |  file name|     path|               vault path|time added
-----------------------------------------------------------------------------------------------------------------
    1|   test.txt|     test| vaults/tmp8/00000/256.7z| 2024-03-30 11:44:50
    2| letter.txt|     test|  vaults/tmp8/00000/95.7z| 2024-03-30 11:48:44
    3|       mtab| test/etc| vaults/tmp8/00000/153.7z| 2024-03-30 21:50:42
vault>info 3

id         : 3
file       : mtab
file path  : test/etc
vault path : vaults/tmp8/00000/153.7z
timestamp  : 2024-03-30 21:50:42.351686
vault>
```

### Closing  the Vault

Use `close` to close the vault. This will reencrypt the database which was open until now for operations.

```
vault vaults/tmp8 opened
vault>list
Number of files in the vault: 2
id   |  file name| path|               vault path|time added
-----------------------------------------------------------------------------------------------------------------
    1|   test.txt| test| vaults/tmp8/00000/256.7z| 2024-03-30 11:44:50
    2| letter.txt| test|  vaults/tmp8/00000/95.7z| 2024-03-30 11:48:44
vault>close
vault vaults/tmp8 closed
vault>
```


