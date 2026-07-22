import unittest
from src.recovery.seed.bip39_validator import BIP39Validator

class TestBIP39Validator(unittest.TestCase):
    def setUp(self):
        self.validator = BIP39Validator()

    def test_valid_bip39_checksum(self):
        # Known valid 12-word BIP39 seed phrase
        valid_seed = ["abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "about"]
        self.assertTrue(self.validator.validate_checksum(valid_seed))

    def test_invalid_bip39_checksum(self):
        # Known invalid checksum (last word incorrect)
        invalid_seed = ["abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon"]
        self.assertFalse(self.validator.validate_checksum(invalid_seed))

if __name__ == "__main__":
    unittest.main()
