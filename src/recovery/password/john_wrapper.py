"""
John the Ripper wrapper – CPU fallback.
"""

import subprocess
import logging
import time
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

class JohnWrapper:
    def __init__(self, john_bin: str = "john"):
        self.john_bin = john_bin

    def run_attack(self, hash_file: Path, wordlist: Path, timeout_hours: int = 24) -> Dict:
        if not hash_file.exists():
            return {"success": False, "error": "Hash file not found"}
        cmd = [
            self.john_bin,
            "--format=exodus",
            "--wordlist=" + str(wordlist),
            str(hash_file),
        ]
        start = time.time()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_hours*3600, check=False)
            elapsed = time.time() - start
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout after {timeout_hours}h"}
        output = proc.stdout + proc.stderr
        success = "password" in output.lower() and "cracked" in output.lower()
        password = None
        if success:
            # Parse john's output: it often prints "password" in the pot file
            pot_file = Path.home() / ".john" / "john.pot"
            if pot_file.exists():
                lines = pot_file.read_text().splitlines()
                for line in lines:
                    if ":" in line:
                        parts = line.split(":", 1)
                        if len(parts) == 2 and "$exodus$" in parts[0]:
                            password = parts[1].strip()
                            break
        return {
            "success": success,
            "password": password,
            "time_seconds": elapsed,
            "method": "john",
            "stdout": output[:500],
        }
