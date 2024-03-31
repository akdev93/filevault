
from pathlib import Path
import sqlite3
import random
from encr import Encryptor
from encr import KeyGenerators
from encr import EncryptionException
import sys
import shlex
import traceback
import datetime
import shutil
import textwrap

# 

class VaultRegistry:


    def __init__(self, directoryPath, create):
        self.directoryPath = directoryPath
        if(create):
            self.create()
        else:
            self.load()
        

    def create(self):
        if(Path(f"{self.directoryPath}/file-vault.db").exists()):
            raise Exception(f"vault already exists: {self.directoryPath}/file-vault.db")

        self.load()
        self.cursor.execute("CREATE TABLE vault_registry(id integer primary key, name TEXT, source_file_path TEXT, vault_file_path TEXT, encryption_key TEXT, insert_ts timestamp)")
        print("Created table vault_registry")
        self.cursor.execute("CREATE TABLE vault_config(config TEXT primary key, value TEXT)")
        print("created table vault_config")


    def readConfig(self):
        result = self.cursor.execute(f"select config, value from vault_config")
        configMap = {}
        for row in result:
            configMap[row[0]] = row[1]
        minKeySize = int(configMap.get("min_keysize", "50"))
        maxKeySize = int(configMap.get("max_keysize", "100"))
        maxFilesPerDirectory = int(configMap.get("max_files_per_dir", 200))

        return VaultConfig(minKeySize, maxKeySize, maxFilesPerDirectory)
        

    def updateConfig(self, config, value):
        self.cursor.execute(f"delete from vault_config where config='{config}'")
        self.cursor.execute(f"insert into vault_config(config, value) values ('{config}', '{value}')")
        self.connection.commit()
        return self.readConfig()


    def load(self):
        self.vaultDir = Path(self.directoryPath)
        self.connection = sqlite3.connect(f"{self.vaultDir}/file-vault.db",  detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.cursor = self.connection.cursor()

    def getFileInfoById(self, id):
        result = self.cursor.execute(f"select id, name, source_file_path, vault_file_path,  encryption_key, insert_ts from vault_registry where id={id}")
        row = result.fetchone()
        if(row is None):
            raise FileNotFoundError(f"No file found with id {id} in vault")
        return FileInfo(row[0], row[1], row[2], row[3], row[4], row[5])

    def searchFiles(self, name):
        print(f"Number of files in the vault: {self.size()}")
        result = self.cursor.execute(f"select id, name, source_file_path, vault_file_path, encryption_key, insert_ts from vault_registry where name like '%{name}%'")
        files = []
        for row in result:
            files.append(FileInfo(row[0], row[1], row[2], row[3], row[4], row[5]))
        return files

    def listFiles(self):
        return self.searchFiles("")

    def size(self):
        result = self.cursor.execute("select count(id) from vault_registry")
        return result.fetchone()[0]
           

    def saveFileInfo(self, fileInfo):
        if(fileInfo.id == 0 ):
            self.cursor.execute(f"Insert into vault_registry (id, name, source_file_path, vault_file_path, encryption_key, insert_ts) values (null, '{fileInfo.fileName}', '{fileInfo.filePath}','{fileInfo.vaultPath}','{fileInfo.encryptionKey}', '{fileInfo.insertTimestamp}') returning id")
            fileInfo.id = self.cursor.fetchone()[0]
        else:
            print(f"update vault_registry set name = '{fileInfo.fileName}', source_file_path = '{fileInfo.filePath}', vault_file_path = '{fileInfo.vaultPath}', encryption_key = '{fileInfo.encryptionKey}' where id = {fileInfo.id}")
            self.cursor.execute(f"update vault_registry set name = '{fileInfo.fileName}', source_file_path = '{fileInfo.filePath}', vault_file_path = '{fileInfo.vaultPath}', encryption_key = '{fileInfo.encryptionKey}' where id = {fileInfo.id}")

        self.connection.commit()
        return fileInfo

    def close(self):
        self.connection.close()


class VaultConfig:

    def __init__(self, minKeySize = 100, maxKeySize = 128, maxFilesPerDirectory = 10):
        self.minKeySize = minKeySize
        self.maxKeySize = maxKeySize
        self.maxFilesPerDirectory = maxFilesPerDirectory
        



class FileInfo: 

    def __init__(self, id, fileName, filePath, vaultPath, encryptionKey, insertTimestamp):
        self.id = id
        self.fileName = fileName
        self.filePath = filePath
        self.vaultPath = vaultPath
        self.encryptionKey = encryptionKey
        self.insertTimestamp = insertTimestamp


class Vault:

    def __init__(self, vaultRegistry):
        self.vaultRegistry = vaultRegistry
        self.vaultConfig = self.vaultRegistry.readConfig()


    def stash(self, file):
        key = KeyGenerators.randomKeyOfSizeRange(self.vaultConfig.minKeySize, self.vaultConfig.maxKeySize)
        encryptor = Encryptor(lambda: key)
        filePath = Path(file)
        if(not filePath.exists()):
            raise Exception(f"{file} doesn't exist")

        subDir = "{:05d}".format(int(self.vaultRegistry.size() / self.vaultConfig.maxFilesPerDirectory))
        vaultDirPath = Path(f"{self.vaultRegistry.directoryPath}/{subDir}/")
        vaultDirPath.mkdir(exist_ok=True)

        vaultFilePath = Path(f"{vaultDirPath}/{random.randint(0,256)}.7z")
        while(vaultFilePath.exists()):
            vaultFilePath = Path(f"{vaultDirPath}/{random.randint(0,256)}.7z")
        
        encryptor.encryptFile2(file, vaultDirPath.as_posix(), vaultFilePath.name)
        fileInfo = self.vaultRegistry.saveFileInfo(FileInfo(0, filePath.name, filePath.parent.as_posix(), vaultFilePath.as_posix(), key, datetime.datetime.now()))
        Path(file).unlink()
        return fileInfo

    
    def retrieve(self, id):
        fileInfo = self.vaultRegistry.getFileInfoById(id)
        encryptor = Encryptor(lambda:fileInfo.encryptionKey)
        encryptor.decryptFile(fileInfo.vaultPath, fileInfo.filePath)

    def updateConfig(self, key, value):
        self.vaultConfig = self.vaultRegistry.updateConfig(key, value)



class VaultCommands:

    def __init__(self):
        self.vault = None

    def create(self, args):
        if(len(args) != 2):
            raise ValueError("Invalid number of arguments for create command")


        vaultPath = args[0]
        keyFile = args[1]
        if(not Path(vaultPath).exists()):
            print(f"[ERROR] path {vaultPath} doesn't exist")
            return

        if((not Path(vaultPath).is_dir()) or (len([c for c in Path(vaultPath).iterdir()]) != 0)):
            print(f"[ERROR] path {vaultPath} is not an empty directory")
            return

        if(Path(keyFile).exists()):
            print(f"Key {keyFile} already exists")
            return

        vaultRegistry = VaultRegistry(vaultPath, True)
        vaultRegistry.close()
        
        key = KeyGenerators.randomKey(1024)
        encryptor = Encryptor(lambda:key)
        try:
            encryptor.encryptFile2(f"{vaultRegistry.directoryPath}/file-vault.db", f"{vaultRegistry.directoryPath}", "file-vault.db.7z")
        except EncryptionException:
            print("[ERROR] encryption of the database failed. Could not create vault")
            return
        file = open(keyFile,"w")
        file.write(key)
        file.close()
        Path(f"{vaultRegistry.directoryPath}/file-vault.db").unlink()
        print(f"vault created at {vaultPath}. The vault is NOT open. Please open the vault with the key file {keyFile} to start using it.")
        print(f"!!!WARNING!!! -> Pleae store the key {keyFile} in a secure place")
        return


    def open(self, args):

        if(len(args) != 2):
            raise ValueError("Invalid number of arguments for open command")

        if(not self.vault is None):
            print(f"[ERROR] vault already open {self.vault.vaultRegistry.directoryPath}")
            return 

        if(not Path(args[1]).exists()):
            print(f"[ERROR] key file {args[1]} not found")
            return 

        self.keyFile = args[1]
        encryptor = Encryptor(lambda: KeyGenerators.fromFile(args[1]))

        try:
            encryptor.decryptFile(f"{args[0]}/file-vault.db.7z", args[0])
        except EncryptionException:
            print("[ERROR] decryption of the database failed. vault cannot be opened")
            return True

        vaultRegistry = VaultRegistry(args[0], False)
        self.vault = Vault(vaultRegistry)
        print(f"vault {args[0]} opened")


    def listFiles(self, args):
        if(self.vault is None):
            print("No vault is open")
            return 
        else:
            if(len(args) == 0):
                searchString = ""
            else:
                searchString = args[0]

        results = self.vault.vaultRegistry.searchFiles(searchString)
        # Pretty formatting... 
        # Is there a better way without including external libraries?
        # (looked at pretty table and tabulate)
        maxVP = max(list(map(lambda x: len(x), list(map(lambda x: x.vaultPath, results)))))
        maxFP = max(list(map(lambda x: len(x), list(map(lambda x: x.filePath, results)))))
        maxFN = max(list(map(lambda x: len(x), list(map(lambda x: x.fileName, results)))))
        headings = ["id", "file name", "path", "vault path", "time added"]
        print(f"{headings[0]:5s}| {headings[1]:>{maxFN}s}| {headings[2]:>{maxFP}s}| {headings[3]:>{maxVP}s}|time added")
        print(f"-----------------------------------------------------------------------------------------------------------------")

        for f in results:
            print(f"{f.id:5d}| {f.fileName:>{maxFN}s}| {f.filePath:>{maxFP}s}| {f.vaultPath:>{maxVP}s}| {str(f.insertTimestamp)[:-7]}")


    def close(self,args):
        if(self.vault is None):
            print("No open vaults.")
            return 

        self.vault.vaultRegistry.close()
        encryptor = Encryptor(lambda: KeyGenerators.fromFile(self.keyFile))
        try:
            encryptor.encryptFile2(f"{self.vault.vaultRegistry.directoryPath}/file-vault.db", f"{self.vault.vaultRegistry.directoryPath}", "file-vault.db.7z")
        except EncryptionException:
            print("[ERROR] encryption of the database failed. Could not close vault.")
            return 
        Path(f"{self.vault.vaultRegistry.directoryPath}/file-vault.db").unlink()
        print(f"vault {self.vault.vaultRegistry.directoryPath} closed")
        self.vault = None
        
    

    def stash(self, args):

        if(len(args) != 1):
            raise ValueError("Invalid number of arguments for stash command")

        if(self.vault is None):
            print("No vault is open")
            return 

        if(not Path(args[0]).exists()):
            print(f"File {args[0]} not found")
            return 
            
        fi = self.vault.stash(args[0])
        self.printFileInfo(fi)


    def stashDirectory(self, args):

        if(len(args) != 1):
            raise ValueError("Invalid number of arguments for stash_directory command")

        dirPath = Path(args[0])

        if(not dirPath.is_dir()):
            raise ValueError(f"Invalid directory path : {dirPath}")

        for filePath in dirPath.iterdir():
            if(filePath.is_file()):
                self.stash([filePath.as_posix()])


    def info(self, args):
        if(len(args) != 1):
            raise ValueError("Invalid number of arguments for info command")

        if(self.vault is None):
            print("No vault is open")
            return 

        fileInfo = self.vault.vaultRegistry.getFileInfoById(args[0])
        if(not fileInfo is None):
            self.printFileInfo(fileInfo)


    def printFileInfo(self, fi):
        print("")
        print(f"id         : {fi.id}")
        print(f"file       : {fi.fileName}")
        print(f"file path  : {fi.filePath}")
        print(f"vault path : {fi.vaultPath}")
        print(f"timestamp  : {fi.insertTimestamp}")



    def retrieve(self, args):
        if(len(args) !=1):
            raise ValueError("Invalid number of arguments for retrieve command")

        if(self.vault is None):
            print("No vault is open")
            return 
        try:
            self.vault.retrieve(args[0])
        except Exception as e:
            print(f"Unable to retrieve {args[0]}: {str(e)}")

    def help(self, args):
        if(len(args) == 0):
            print("Commands:")
            for key in command_usage.keys():
                print(f"{key:20s}: {command_usage.get(key)}")
            return
        if(len(args) == 1):
            print(f"Usage: {command_usage.get(args[0])}")
        else:
            raise ValueError("Invalid Number of arguments for the help command")

    def config(self, args):
        if(len(args) != 2):
            raise ValueError("Invalid number of arguments for config")

        if(self.vault is None):
            print("No vault is open")
            return

        self.vault.updateConfig(args[0], args[1])




commands = {
        "open": lambda args: vc.open(args),
        "list": lambda args: vc.listFiles(args),
        "stash": lambda args: vc.stash(args),
        "retrieve": lambda args: vc.retrieve(args),
        "create": lambda args: vc.create(args),
        "close": lambda args: vc.close(args),
        "help": lambda args: vc.help(args),
        "config": lambda args: vc.config(args),
        "stash_directory": lambda args: vc.stashDirectory(args),
        "info": lambda args: vc.info(args)
        }

command_usage = {
        "create": "create <path to new vault> <key file>",
        "open": "open <path to vault> <key file>",
        "list": "list <file pattern>",
        "stash": "stash <file with path>",
        "retrieve": "retrieve <vault file id>",
        "create": "create <path to vault> <key file>",
        "close": "close",
        "help": "help <command>",
        "config": "config <config> <value>",
        "stash_directory": "stash_directory <directory>",
        "info": "info <id>"
        }



def prompt():
    sys.stdout.write("vault>")
    sys.stdout.flush()

if(shutil.which("7z") is None):
    print("7z not found in path. Please add it to path and try again")
    sys.exit()

if __name__ == '__main__':
    vc = VaultCommands()
    prompt()
        

    for line in sys.stdin:
        if "EXIT" == line.rstrip().upper():
            commands.get("close")([])
            break
        else:
            if not line.rstrip() == "":
                s = shlex.split(line)
                cmdProcessed = False
                try:
                    commands.get(s[0],lambda args: print("invalid command"))(s[1::])
                except ValueError as ve:
                    print(f"[ERROR]: Usage: {command_usage.get(s[0])}")
                except Exception:
                    print("[ERROR] : Command Failed with an exception. Please backup the database ASAP")
                    traceback.print_exc()
            prompt()


