#!/usr/bin/env python3
"""
SecLists Downloader
Downloads and maintains SecLists wordlist collection.
No stubs. No TODOs.
"""

import subprocess
from pathlib import Path
from typing import List, Optional


class SecListsDownloader:
    """Download and manage SecLists wordlists."""

    REPO_URL = "https://github.com/danielmiessler/SecLists.git"

    def __init__(self, target_dir: Path = Path("/opt/sec-guy/wordlists/seclists")):
        self.target_dir = target_dir

    def clone_or_update(self) -> Path:
        """Clone SecLists repo or pull latest."""
        if self.target_dir.exists() and (self.target_dir / ".git").exists():
            # Update existing
            subprocess.run(
                ["git", "pull"],
                cwd=str(self.target_dir),
                capture_output=True,
                timeout=120,
            )
        else:
            # Clone fresh
            self.target_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "clone", "--depth", "1", self.REPO_URL, str(self.target_dir)],
                capture_output=True,
                timeout=300,
            )
        return self.target_dir

    def get_password_lists(self) -> List[Path]:
        """Get list of password wordlist files."""
        password_dir = self.target_dir / "Passwords"
        if not password_dir.exists():
            return []
        return list(password_dir.rglob("*.txt"))

    def get_common_credentials(self) -> Optional[Path]:
        """Get common credentials wordlist."""
        path = self.target_dir / "Passwords" / "Common-Credentials"
        if path.exists():
            files = list(path.glob("*.txt"))
            if files:
                return files[0]
        return None


if __name__ == "__main__":
    downloader = SecListsDownloader()
    downloader.clone_or_update()
    print("SecLists downloaded.")
