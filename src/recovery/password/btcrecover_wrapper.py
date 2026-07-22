"""
BTCRecover wrapper – fully integrated.
"""

import subprocess
import logging
import time
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class BTCRecoverWrapper:
    def __init__(self, btcrecover_path: Path = None):
        if btcrecover_path is None:
            btcrecover_path = Path(__file__).parent.parent.parent.parent / "sec-guy" / "tools" / "btcrecover.py"
        self.script = btcrecover_path
        if not self.script.exists():
            logger.warning(f"btcrecover.py not found at {self.script}")

    def recover_password(self, wallet_path: Path, hints: str = "", tokenlist: Optional[Path] = None,
                         timeout_hours: int = 24) -> Dict:
        if not self.script.exists():
            return {"success": False, "error": f"btcrecover.py not found at {self.script}"}
        cmd = [
            "python", str(self.script),
            "--wallet", str(wallet_path),
            "--typos", "0",  # no typo expansion to speed up
            "--timeout", str(timeout_hours * 3600),
        ]
        if hints:
            cmd.extend(["--hints", hints])
        if tokenlist and tokenlist.exists():
            cmd.extend(["--tokenlist", str(tokenlist)])
        start = time.time()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_hours*3600, check=False)
            elapsed = time.time() - start
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout after {timeout_hours}h"}
        output = proc.stdout + proc.stderr
        success = "Found password:" in output
        password = None
        if success:
            for line in output.splitlines():
                if "Found password:" in line:
                    password = line.split("Found password:")[-1].strip()
                    break
        return {
            "success": success,
            "password": password,
            "time_seconds": elapsed,
            "method": "btcrecover",
            "stdout": output[:500],
        }
