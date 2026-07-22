"""
SeedRecover wrapper – calls seedrecover.py.
"""

import subprocess
import logging
import time
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

class SeedRecoverWrapper:
    def __init__(self, script_path: Path = None):
        if script_path is None:
            script_path = Path(__file__).parent.parent.parent.parent / "sec-guy" / "tools" / "seedrecover.py"
        self.script = script_path

    def recover_seed(
        self,
        partial_words: List[str],
        wallet_file: Path,
        missing_positions: List[int],
        timeout_seconds: int = 86400,
        wallet_type: str = "exodus"
    ) -> Tuple[Optional[List[str]], Optional[str]]:
        if not self.script.exists():
            return None, f"seedrecover.py not found at {self.script}"
        cmd = [
            "python", str(self.script),
            "--wallet", str(wallet_file),
            "--wallet-type", wallet_type,
            "--addr-limit", "10",
            "--timeout", str(timeout_seconds),
            "--partial", " ".join(partial_words),
            "--missing", ",".join(str(p) for p in missing_positions),
        ]
        time.time()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds, check=False)
        except subprocess.TimeoutExpired:
            return None, f"Timeout after {timeout_seconds}s"
        output = proc.stdout + proc.stderr
        for line in output.splitlines():
            if "Recovered seed:" in line or "Found seed:" in line:
                seed_part = line.split(":", 1)[-1].strip()
                words = seed_part.split()
                if len(words) in (12, 24):
                    return words, None
            if "Mnemonic:" in line:
                seed_part = line.split(":", 1)[-1].strip()
                words = seed_part.split()
                if len(words) in (12, 24):
                    return words, None
        return None, "Seed not found"