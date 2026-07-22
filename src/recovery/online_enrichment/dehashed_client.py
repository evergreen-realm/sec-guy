"""
DeHashed breach data client.
"""

import requests
import logging
from typing import List

logger = logging.getLogger(__name__)


class DeHashedClient:
    def __init__(self, api_key: str = None, email: str = None):
        self.api_key = api_key
        self.email = email
        self.base_url = "https://api.dehashed.com"

    def get_password_patterns(self, query: str = "") -> List[str]:
        """
        Fetch passwords from DeHashed for a given query (e.g., domain).
        """
        if not self.api_key or not self.email:
            logger.warning("DeHashed credentials not set")
            return []

        auth = (self.email, self.api_key)
        url = f"{self.base_url}/search"
        params = {"query": query, "size": 100}
        try:
            resp = requests.get(url, auth=auth, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                entries = data.get("entries", [])
                passwords = [e.get("password") for e in entries if e.get("password")]
                return passwords[:50]  # limit
            else:
                logger.error(f"DeHashed error: {resp.status_code}")
        except Exception as e:
            logger.error(f"DeHashed request failed: {e}")
        return []
