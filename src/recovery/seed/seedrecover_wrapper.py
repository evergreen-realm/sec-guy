"""
Wrapper for BTCRecover seed recovery.
"""

from pathlib import Path
from typing import List, Optional, Tuple
import subprocess
import logging
import time

logger = logging.getLogger(__name__)


class SeedRecoverWrapper:
    def __init__(self, btcrecover_path: Optional[Path] = None):
        if btcrecover_path is None:
            btcrecover_path = Path(__file__).parent.parent.parent.parent / "tools" / "btcrecover"
        self.btcrecover_path = btcrecover_path
        self.seedrecover_script = self.btcrecover_path / "seedrecover.py"
        if not self.seedrecover_script.exists():
            logger.warning(f"seedrecover.py not found at {self.seedrecover_script}")

    def recover_seed(
        self,
        partial_words: List[str],
        wallet_file: Path,
        missing_positions: List[int],
        timeout_seconds: int = 86400,
        wallet_type: str = "exodus"
    ) -> Tuple[Optional[List[str]], Optional[str]]:
        if not self.seedrecover_script.exists():
            return None, f"seedrecover.py not found at {self.seedrecover_script}"

        cmd = [
            "python", str(self.seedrecover_script),
            "--wallet-type", wallet_type,
            "--wallet-file", str(wallet_file),
            "--partial", " ".join(partial_words),
            "--missing", ",".join(str(p) for p in missing_positions),
            "--timeout", str(timeout_seconds),
            "--address-limit", "10",
        ]

        logger.info(f"Running seedrecover: {' '.join(cmd)}")
        start = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False
            )
        except subprocess.TimeoutExpired:
            return None, "Seed recovery timed out"

        output = result.stdout + result.stderr
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

        return None, "Seed not recovered" + (f": {output[:200]}" if output else "")