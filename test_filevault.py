import unittest
from filevault import VaultCommands
from pathlib import Path
import tempfile
import shutil
import secrets
import random
import hashlib

class TestVaultCommandMethods(unittest.TestCase):

    def setUp(self):
        self.testRootDir = tempfile.mkdtemp(suffix = "vault", prefix="test.")
        print(f"root dir: {self.testRootDir}")
        self.keyFile = f"{self.testRootDir}/key"
        self.vaultDir = f"{self.testRootDir}/vault"
        self.sourceDir = f"{self.testRootDir}/source"
        Path(self.vaultDir).mkdir()
        Path(self.sourceDir).mkdir()

    def test_open_invalid_args(self):
        vc = VaultCommands()
        with self.assertRaises(ValueError):
            vc.open([])

    def test_open_InvalidPaths(self):
        vc = VaultCommands()
        vc.open(["/non-existing-path", "no-such-key"])
        self.assertTrue(vc.vault is None)

    def test_open_validKeyNoPath(self):
        keyFile = open("_test_key", "w")
        keyFile.write("key")
        keyFile.close()

        vc = VaultCommands()
        vc.open(["/non-existing-path", "_test_key"])
        self.assertTrue(vc.vault is None)
        Path("_test_key").unlink()


    def test_create(self):

        vc = VaultCommands()
        vc.create([self.vaultDir, self.keyFile])
        self.assertTrue(Path(self.keyFile).stat().st_size > 0)
        self.assertTrue(Path(f"{self.vaultDir}/file-vault.db.7z").exists())

    def test_create_empty_args(self):
        vc = VaultCommands()
        with self.assertRaises(ValueError):
            vc.create([])

    def test_create_invalid_args(self):
        vc = VaultCommands()
        with self.assertRaises(ValueError):
            vc.create([self.vaultDir])

    def test_stash_invalid_args(self):
        vc = VaultCommands()
        with self.assertRaises(ValueError):
            vc.stash([])

    def test_retrieve_invalid_args(self):
        vc = VaultCommands()
        with self.assertRaises(ValueError):
            vc.retrieve([])

    def test_stash(self):
        vc = VaultCommands()
        vc.create([self.vaultDir, self.keyFile])
        vc.open([self.vaultDir, self.keyFile])
        testFiles = self.createTestFiles(self.sourceDir, 5)
        for file in testFiles:
            vc.stash([file])
            self.assertFalse(Path(file).exists())
            self.assertTrue(len(vc.vault.vaultRegistry.searchFiles(Path(file).name)) == 1)
        vc.close([])

    def test_stash_retrieve(self):
        vc = VaultCommands()
        vc.create([self.vaultDir, self.keyFile])
        vc.open([self.vaultDir, self.keyFile])
        testFiles = self.createTestFiles(self.sourceDir, 5)
        for file in testFiles:
            hash = hashlib.sha1(Path(file).read_bytes()).hexdigest()
            vc.stash([file])
            self.assertFalse(Path(file).exists())
            self.assertTrue(len(vc.vault.vaultRegistry.searchFiles(Path(file).name)) == 1)
            id = vc.vault.vaultRegistry.searchFiles(Path(file).name)[0].id
            vc.retrieve([id])
            self.assertTrue(Path(file).exists())
            self.assertTrue(hashlib.sha1(Path(file).read_bytes()).hexdigest() == hash)

        vc.close([])

    def test_stash_directory_retrieve(self):
        fileHashes = {}
        vc = VaultCommands()
        vc.create([self.vaultDir, self.keyFile])
        vc.open([self.vaultDir, self.keyFile])

        subdir = f"{self.sourceDir}/sub-dir1"
        Path(subdir).mkdir()
        subDirTestFiles = self.createTestFiles(subdir, 10)

        testFiles = self.createTestFiles(self.sourceDir, 5)
        for file in testFiles:
            hash = hashlib.sha1(Path(file).read_bytes()).hexdigest()
            fileHashes[file] = hash
        vc.stashDirectory([self.sourceDir])

        # all files in the subdirectory should remain
        for file in subDirTestFiles:
            self.assertTrue(Path(file).exists())

        # all files in the directory should no longer exist
        for file in testFiles:
            self.assertFalse(Path(file).exists())
            self.assertTrue(len(vc.vault.vaultRegistry.searchFiles(Path(file).name)) == 1)

        # all files should be retrieved from the vault and prove to be similar
        for file in testFiles:
            id = vc.vault.vaultRegistry.searchFiles(Path(file).name)[0].id
            vc.retrieve([id])
            self.assertTrue(Path(file).exists())
            self.assertTrue(hashlib.sha1(Path(file).read_bytes()).hexdigest() == fileHashes[file])

        vc.close([])


    def createTestFiles(self, dir, count):
        testFiles = []
        for num in range(0,count):
            data = secrets.token_urlsafe(random.randint(0,num*1000))
            p = Path(f"{dir}/file-{num}.txt")
            p.write_text(data)
            testFiles.append(p.as_posix())
        return testFiles
            
    def tearDown(self):
        print(f"del:{self.testRootDir}")
        shutil.rmtree(self.testRootDir)


