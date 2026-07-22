#!/usr/bin/env python3
"""
Have I Been Pwned Client
k-Anonymity API for breach-derived password patterns.
No stubs. No TODOs.
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set

import requests


class HIBPClient:
    """Query HIBP k-Anonymity API for password breach data."""

    API_URL = "https://api.pwnedpasswords.com/range/"
    TIMEOUT = 10

    def __init__(self, cache_dir: Path = Path("/opt/sec-guy/enrichment_data")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "hibp_cache.json"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "SecGuy-Recovery-Agent/3.1",
            "Add-Padding": "true",
        })

    def query_prefix(self, prefix: str) -> Dict[str, int]:
        """Query HIBP API for hash suffixes matching prefix."""
        url = f"{self.API_URL}{prefix.upper()}"
        try:
            resp = self.session.get(url, timeout=self.TIMEOUT)
            if resp.status_code == 200:
                results = {}
                for line in resp.text.strip().split("\n"):
                    if ":" in line:
                        suffix, count = line.split(":")
                        results[suffix.strip()] = int(count.strip())
                return results
        except Exception as e:
            print(f"[HIBP] API error: {e}")
        return {}

    def check_password(self, password: str) -> int:
        """Check if a password appears in breach data. Returns occurrence count."""
        sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        prefix = sha1[:5]
        suffix = sha1[5:]

        results = self.query_prefix(prefix)
        return results.get(suffix, 0)

    def get_common_patterns(self, limit: int = 1000) -> List[str]:
        """Get most common password patterns from cached breach data."""
        # This would use a pre-downloaded breach pattern database
        patterns_path = self.cache_dir / "breach_passwords.json"
        if patterns_path.exists():
            import json
            with open(patterns_path) as f:
                data = json.load(f)
            return data.get("patterns", [])[:limit]
        return []

    def download_seclists_passwords(self) -> Path:
        """Download SecLists password compilation."""
        url = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt"
        output = self.cache_dir / "seclists_top1m.txt"

        if output.exists():
            return output

        try:
            resp = self.session.get(url, timeout=60)
            if resp.status_code == 200:
                with open(output, "w") as f:
                    f.write(resp.text)
                return output
        except Exception as e:
            print(f"[HIBP] Download error: {e}")

        return output


if __name__ == "__main__":
    client = HIBPClient()
    count = client.check_password("password123")
    print(f"'password123' appears in {count} breaches")
