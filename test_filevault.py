import unittest
from filevault import VaultCommands

class TestVaultCommandMethods(unittest.TestCase):

    def test_open_invalid_args(self):
        vc = VaultCommands()
        with self.assertRaises(ValueError):
            vc.open([])

    def test_open_InvalidPaths(self):
        vc = VaultCommands()
        vc.open(["/non-existing-path", "no-such-key"])
        self.assertTrue(vc.vault is None)
