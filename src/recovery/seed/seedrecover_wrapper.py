"""
Wrapper for BTCRecover seed recovery.
This module provides an interface to seedrecover.py for BIP39 reconstruction.
"""

from pathlib import Path
from typing import List, Optional, Tuple
import subprocess
import json
import logging

logger = logging.getLogger(__name__)


class SeedRecoverWrapper:
    """
    Orchestrates BIP39 seed phrase recovery using BTCRecover's seedrecover.py.
    All operations are logged and require explicit user authorization.
    """

    def __init__(self, btcrecover_path: Optional[Path] = None):
        self.btcrecover_path = btcrecover_path or Path("tools/btcrecover")
        self.seedrecover_script = self.btcrecover_path / "seedrecover.py"
        if not self.seedrecover_script.exists():
            logger.warning("seedrecover.py not found at %s", self.seedrecover_script)

    def recover_seed(
        self,
        partial_words: List[str],
        wallet_file: Path,
        missing_positions: List[int],
        timeout_seconds: int = 86400,
        wallet_type: str = "exodus"
    ) -> Tuple[Optional[List[str]], Optional[str]]:
        """
        Recover missing BIP39 seed words via seedrecover.py.
        """
        if not self.seedrecover_script.exists():
            return None, f"seedrecover.py not found at {self.seedrecover_script}"

        mnemonic_str = " ".join(partial_words)
        cmd = [
            "python3",
            str(self.seedrecover_script),
            "--mnemonic", mnemonic_str,
            "--wallet-type", wallet_type,
            "--dsw",
        ]
        if wallet_file and wallet_file.exists():
            cmd.extend(["--wallet", str(wallet_file)])

        for pos in missing_positions:
            cmd.extend(["--missing-word", str(pos)])

        logger.info("Executing seedrecover with command: %s", " ".join(cmd))
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=str(self.btcrecover_path)
            )

            stdout = result.stdout
            if "Seed found:" in stdout:
                for line in stdout.splitlines():
                    if "Seed found:" in line:
                        seed_str = line.split("Seed found:")[1].strip()
                        recovered_words = seed_str.split()
                        return recovered_words, None
            return None, "Seed phrase not found within specified search space"

        except subprocess.TimeoutExpired:
            return None, f"Execution timed out after {timeout_seconds} seconds"
        except Exception as e:
            logger.exception("Error executing seedrecover: %s", e)
            return None, str(e)

    def verify_seed(self, seed_words: List[str], address: str) -> bool:
        """Verify seed words against a expected blockchain address."""
        try:
            from .bip39_validator import BIP39Validator
            if not BIP39Validator.validate_mnemonic(seed_words):
                return False
            from .address_verifier import AddressVerifier
            verifier = AddressVerifier()
            verification = verifier.verify_seed(" ".join(seed_words), expected_address=address)
            return verification.get("match", False)
        except Exception as e:
            logger.error("Failed to verify seed: %s", e)
            return False