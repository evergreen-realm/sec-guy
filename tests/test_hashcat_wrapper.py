import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.recovery.password.hashcat_wrapper import HashcatExodusWrapper

class TestHashcatWrapper(unittest.TestCase):
    def setUp(self):
        self.wrapper = HashcatExodusWrapper()

    @patch("subprocess.run")
    def test_run_tokenlist_attack_command_building(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Status: Cracked"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        with patch.object(self.wrapper, "_extract_hash", return_value="$exodus$N=16384,r=8,p=1,data=00"):
            with patch("pathlib.Path.read_text", return_value="password123"):
                with patch("pathlib.Path.exists", return_value=True):
                    res = self.wrapper.run_tokenlist_attack(
                        wallet_path=Path("test.hash"),
                        tokenlist=Path("tokens.txt"),
                        output_file=Path("out.txt"),
                        timeout_hours=1
                    )
                    self.assertTrue(res.get("success"))
                    self.assertEqual(res.get("password"), "password123")

if __name__ == "__main__":
    unittest.main()
