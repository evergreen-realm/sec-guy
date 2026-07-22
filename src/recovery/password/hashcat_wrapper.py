"""
Hashcat Exodus wrapper – fully integrated with installed binary.
"""

import subprocess
import logging
import time
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class HashcatExodusWrapper:
    def __init__(self, hashcat_bin: str = "hashcat", tools_dir: Path = None):
        self.hashcat_bin = hashcat_bin
        if tools_dir is None:
            tools_dir = Path(__file__).parent.parent.parent.parent / "sec-guy" / "tools"
        self.exodus2hashcat = tools_dir / "exodus2hashcat.py"
        self.work_dir = tools_dir / "tmp"
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def _extract_hash(self, wallet_path: Path) -> Optional[str]:
        """Extract Exodus hash using exodus2hashcat.py."""
        if not self.exodus2hashcat.exists():
            logger.error(f"exodus2hashcat.py not found at {self.exodus2hashcat}")
            return None
        cmd = ["python", str(self.exodus2hashcat), str(wallet_path)]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
            if result.returncode == 0:
                hash_line = result.stdout.strip()
                if hash_line.startswith("$exodus$"):
                    return hash_line
            logger.error(f"extraction failed: {result.stderr}")
        except Exception as e:
            logger.exception(f"extraction error: {e}")
        return None

    def run_tokenlist_attack(self, wallet_path: Path, tokenlist: Path, output_file: Path,
                             timeout_hours: int = 24) -> Dict:
        """Tokenlist attack mode (-a 0)."""
        hash_line = self._extract_hash(wallet_path)
        if not hash_line:
            return {"success": False, "error": "Hash extraction failed"}
        hash_file = self.work_dir / "hash.txt"
        hash_file.write_text(hash_line + "\n")
        cmd = [
            self.hashcat_bin,
            "-m", "28200",
            "-a", "0",
            "-w", "4",
            "--force",
            str(hash_file),
            str(tokenlist),
            "--status",
            "--status-timer=1",
            "--outfile", str(output_file),
            "--outfile-format", "2",
        ]
        start = time.time()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_hours*3600, check=False)
            elapsed = time.time() - start
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout after {timeout_hours}h"}
        # Parse stdout for success
        output = proc.stdout + proc.stderr
        success = "Status: Cracked" in output or "Recovered" in output
        password = None
        if success:
            # Look for password in output or outfile
            if output_file.exists():
                lines = output_file.read_text().splitlines()
                if lines:
                    password = lines[0].strip()
            if not password:
                for line in output.splitlines():
                    if ":$exodus$" in line:
                        parts = line.split(":", 2)
                        if len(parts) >= 3:
                            password = parts[2].strip()
                            break
        return {
            "success": success,
            "password": password,
            "time_seconds": elapsed,
            "method": "tokenlist",
            "stdout": output[:500],
        }

    def run_mask_attack(self, wallet_path: Path, mask: str, output_file: Path,
                        timeout_hours: int = 24) -> Dict:
        """Mask attack mode (-a 3)."""
        hash_line = self._extract_hash(wallet_path)
        if not hash_line:
            return {"success": False, "error": "Hash extraction failed"}
        hash_file = self.work_dir / "hash.txt"
        hash_file.write_text(hash_line + "\n")
        cmd = [
            self.hashcat_bin,
            "-m", "28200",
            "-a", "3",
            "-w", "4",
            "--force",
            str(hash_file),
            mask,
            "--status",
            "--status-timer=1",
            "--outfile", str(output_file),
            "--outfile-format", "2",
        ]
        start = time.time()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_hours*3600, check=False)
            elapsed = time.time() - start
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout after {timeout_hours}h"}
        output = proc.stdout + proc.stderr
        success = "Status: Cracked" in output
        password = None
        if success and output_file.exists():
            lines = output_file.read_text().splitlines()
            if lines:
                password = lines[0].strip()
        return {
            "success": success,
            "password": password,
            "time_seconds": elapsed,
            "method": "mask",
            "mask": mask,
            "stdout": output[:500],
        }

    def run_rule_attack(self, wallet_path: Path, tokenlist: Path, rule_file: Path,
                        output_file: Path, timeout_hours: int = 24) -> Dict:
        """Rule attack (-a 0 -r)."""
        hash_line = self._extract_hash(wallet_path)
        if not hash_line:
            return {"success": False, "error": "Hash extraction failed"}
        hash_file = self.work_dir / "hash.txt"
        hash_file.write_text(hash_line + "\n")
        cmd = [
            self.hashcat_bin,
            "-m", "28200",
            "-a", "0",
            "-r", str(rule_file),
            "-w", "4",
            "--force",
            str(hash_file),
            str(tokenlist),
            "--status",
            "--status-timer=1",
            "--outfile", str(output_file),
            "--outfile-format", "2",
        ]
        start = time.time()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_hours*3600, check=False)
            elapsed = time.time() - start
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout after {timeout_hours}h"}
        output = proc.stdout + proc.stderr
        success = "Status: Cracked" in output
        password = None
        if success and output_file.exists():
            lines = output_file.read_text().splitlines()
            if lines:
                password = lines[0].strip()
        return {
            "success": success,
            "password": password,
            "time_seconds": elapsed,
            "method": "rule",
            "stdout": output[:500],
        }
