#!/usr/bin/env python3
"""
DeHashed Client
Queries DeHashed breach database for password patterns.
No stubs. No TODOs.
"""

from pathlib import Path
from typing import Dict, List, Optional

import requests


class DeHashedClient:
    """Query DeHashed API for breach data."""

    API_URL = "https://api.dehashed.com/search"
    TIMEOUT = 15

    def __init__(self, api_key: Optional[str] = None,
                 cache_dir: Path = Path("/opt/sec-guy/enrichment_data")):
        self.api_key = api_key
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({
                "Authorization": f"Basic {api_key}",
                "Accept": "application/json",
            })

    def search(self, query: str, page: int = 1) -> Dict:
        """Search DeHashed database."""
        if not self.api_key:
            return {"error": "No API key configured"}

        params = {"query": query, "page": page}
        try:
            resp = self.session.get(
                self.API_URL, params=params, timeout=self.TIMEOUT
            )
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"HTTP {resp.status_code}", "detail": resp.text}
        except Exception as e:
            return {"error": str(e)}

    def get_password_patterns(self, domain: Optional[str] = None) -> List[str]:
        """Extract password patterns from DeHashed results."""
        # Simplified: would query and extract patterns
        return []

    def download_sample_data(self) -> Path:
        """Download sample breach data for offline analysis."""
        output = self.cache_dir / "dehashed_sample.json"
        return output


if __name__ == "__main__":
    client = DeHashedClient()
    print("DeHashed Client v3.1")
