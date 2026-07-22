#!/usr/bin/env python3
"""
Secrets Manager
Manages lifecycle of recovered secrets in the vault.
No stubs. No TODOs.
"""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from src.core.crypto_utils import SecureVault


@dataclass
class VaultEntry:
    entry_id: str
    entry_type: str  # "password", "seed", "2fa_secret"
    created_at: float
    expires_at: float
    metadata: Dict
    accessed_count: int = 0


class SecretsManager:
    """Manage recovered secrets with TTL and access tracking."""

    def __init__(self, vault: Optional[SecureVault] = None,
                 default_ttl: int = 300):
        self.vault = vault or SecureVault()
        self.default_ttl = default_ttl
        self.entries: Dict[str, VaultEntry] = {}

    def store(self, plaintext: str, entry_type: str,
              password: str, metadata: Optional[Dict] = None) -> str:
        """Store a secret in the vault."""
        entry_id = self.vault.encrypt(plaintext, password, metadata)
        now = time.time()
        entry = VaultEntry(
            entry_id=entry_id,
            entry_type=entry_type,
            created_at=now,
            expires_at=now + self.default_ttl,
            metadata=metadata or {},
        )
        self.entries[entry_id] = entry
        return entry_id

    def retrieve(self, entry_id: str, password: str) -> Optional[str]:
        """Retrieve a secret from the vault."""
        entry = self.entries.get(entry_id)
        if not entry:
            return None

        if time.time() > entry.expires_at:
            self.delete(entry_id)
            return None

        entry.accessed_count += 1
        return self.vault.decrypt(entry_id, password)

    def delete(self, entry_id: str) -> bool:
        """Securely delete a vault entry."""
        if entry_id in self.entries:
            self.vault.shred(entry_id)
            del self.entries[entry_id]
            return True
        return False

    def purge_expired(self) -> int:
        """Delete all expired entries. Returns count deleted."""
        now = time.time()
        expired = [eid for eid, e in self.entries.items() if now > e.expires_at]
        for eid in expired:
            self.delete(eid)
        return len(expired)

    def list_entries(self) -> List[VaultEntry]:
        """List all active vault entries."""
        self.purge_expired()
        return list(self.entries.values())

    def get_stats(self) -> Dict:
        """Get vault statistics."""
        return {
            "total_entries": len(self.entries),
            "expired": sum(1 for e in self.entries.values() if time.time() > e.expires_at),
        }


if __name__ == "__main__":
    manager = SecretsManager()
    print("Secrets Manager v3.1")
