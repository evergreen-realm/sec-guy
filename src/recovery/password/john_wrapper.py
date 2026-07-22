#!/usr/bin/env python3
"""
John the Ripper Wrapper
CPU fallback for Exodus wallet hash cracking.
No stubs. No TODOs.
"""

import subprocess
from pathlib import Path
from typing import Dict


class JohnWrapper:
    """Wrapper for John the Ripper Exodus format."""

    FORMAT = "exodus"

    def __init__(self, john_path: str = "john"):
        self.john_path = john_path

    def run_wordlist(self, hash_file: Path, wordlist: Path,
                     timeout_hours: int = 8) -> Dict:
        """Run John with wordlist attack."""
        cmd = [
            self.john_path,
            f"--format={self.FORMAT}",
            "--wordlist", str(wordlist),
            str(hash_file),
        ]

        print("[JOHN] Starting wordlist attack (CPU)...")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True, text=True,
                timeout=timeout_hours * 3600
            )

            # Check for cracked password
            show_cmd = [self.john_path, f"--format={self.FORMAT}", "--show", str(hash_file)]
            show_result = subprocess.run(show_cmd, capture_output=True, text=True, timeout=60)

            for line in show_result.stdout.split("\n"):
                if ":" in line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        password = parts[-1].strip()
                        return {"success": True, "password": password}

            return {"success": False, "error": "Password not found"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_incremental(self, hash_file: Path, max_length: int = 8,
                        timeout_hours: int = 12) -> Dict:
        """Run John incremental (brute-force) mode."""
        cmd = [
            self.john_path,
            f"--format={self.FORMAT}",
            "--incremental",
            f"--max-length={max_length}",
            str(hash_file),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True, text=True,
                timeout=timeout_hours * 3600
            )

            show_cmd = [self.john_path, f"--format={self.FORMAT}", "--show", str(hash_file)]
            show_result = subprocess.run(show_cmd, capture_output=True, text=True, timeout=60)

            for line in show_result.stdout.split("\n"):
                if ":" in line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        password = parts[-1].strip()
                        return {"success": True, "password": password}

            return {"success": False, "error": "Password not found"}

        except Exception as e:
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    wrapper = JohnWrapper()
    print("John the Ripper Wrapper v3.1")
