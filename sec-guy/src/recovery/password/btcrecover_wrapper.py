#!/usr/bin/env python3
"""
BTCRecover Wrapper
Tokenlist attack with semantic expansion for Exodus wallets.
No stubs. No TODOs.
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class BTCRecoverWrapper:
    """Wrapper for BTCRecover tokenlist and seed recovery."""

    def __init__(self, btcrecover_dir: Path = Path("tools/btcrecover")):
        self.btcrecover_dir = btcrecover_dir
        self.btcrpass_path = btcrecover_dir / "btcrecover.py"

    def run_tokenlist(self, wallet_path: Path, tokenlist: Path,
                      wallet_type: str = "exodus",
                      timeout_hours: int = 4) -> Dict:
        """Run BTCRecover with a tokenlist."""
        cmd = [
            "python3", str(self.btcrpass_path),
            "--wallet", str(wallet_path),
            "--tokenlist", str(tokenlist),
            "--typos", "2",
            "--typos-type", "replace",
            "--wallet-type", wallet_type,
            "--dsw",
        ]

        print(f"[BTCRECOVER] Starting tokenlist attack...")
        print(f"[BTCRECOVER] Tokenlist: {tokenlist}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True, text=True,
                timeout=timeout_hours * 3600,
                cwd=str(self.btcrecover_dir)
            )

            stdout = result.stdout
            if "Password found:" in stdout:
                for line in stdout.split("\n"):
                    if "Password found:" in line:
                        password = line.split("Password found:")[1].strip()
                        return {"success": True, "password": password}

            return {"success": False, "error": "Password not found"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_seedrecover(self, seed_words: List[str], missing_positions: List[int],
                        wallet_type: str = "exodus", timeout_hours: int = 24) -> Dict:
        """Run seedrecover for BIP39 seed reconstruction."""
        seed_arg = " ".join(seed_words)
        cmd = [
            "python3", str(self.btcrecover_dir / "seedrecover.py"),
            "--mnemonic", seed_arg,
            "--wallet-type", wallet_type,
            "--dsw",
        ]
        for pos in missing_positions:
            cmd.extend(["--missing-word", str(pos)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True, text=True,
                timeout=timeout_hours * 3600,
                cwd=str(self.btcrecover_dir)
            )

            stdout = result.stdout
            if "Seed found:" in stdout:
                for line in stdout.split("\n"):
                    if "Seed found:" in line:
                        seed = line.split("Seed found:")[1].strip()
                        return {"success": True, "seed_phrase": seed}

            return {"success": False, "error": "Seed not found"}

        except Exception as e:
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    wrapper = BTCRecoverWrapper()
    print("BTCRecover Wrapper v3.1")
