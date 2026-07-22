"""
CUPP wrapper – calls cupp.py to generate candidates.
"""

import subprocess
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

class CUPPWrapper:
    def __init__(self, script_path: Path = None):
        if script_path is None:
            script_path = Path(__file__).parent.parent.parent.parent / "sec-guy" / "tools" / "cupp.py"
        self.script = script_path

    def generate_from_profile(self, profile_dict: dict) -> List[str]:
        """Generate candidates from a user profile (dictionary of personal info)."""
        if not self.script.exists():
            logger.warning("cupp.py not found; returning empty list")
            return []
        # Write profile to a temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            for key, value in profile_dict.items():
                f.write(f"{key}: {value}\n")
            profile_file = Path(f.name)
        cmd = [
            "python", str(self.script),
            "-i",
            "--input", str(profile_file),
            "--output", str(profile_file.parent / "candidates.txt"),
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
        except Exception as e:
            logger.error(f"CUPP failed: {e}")
            return []
        out_file = profile_file.parent / "candidates.txt"
        if out_file.exists():
            candidates = out_file.read_text().splitlines()
            out_file.unlink(missing_ok=True)
            return candidates
        return []
