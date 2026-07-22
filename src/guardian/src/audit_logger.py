#!/usr/bin/env python3
"""
Audit Logger
Append-only audit trail for all recovery operations.
No stubs. No TODOs.
"""

import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from src.core.platform import Platform


class AuditLogger:
    """Tamper-evident audit logging for Sec Guy."""

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Platform.get_log_dir()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "audit.log"
        self.chain_hash = "0" * 64

    def log_event(self, event_type: str, job_id: str,
                  details: Dict, biometric_hash: Optional[str] = None) -> str:
        """Log an auditable event with hash chain."""
        timestamp = time.time()
        entry = {
            "timestamp": timestamp,
            "datetime": datetime.utcfromtimestamp(timestamp).isoformat(),
            "event_type": event_type,
            "job_id": job_id,
            "details": details,
            "biometric_hash": biometric_hash,
            "prev_hash": self.chain_hash,
        }

        # Calculate entry hash
        entry_json = json.dumps(entry, sort_keys=True)
        entry_hash = hashlib.sha256(entry_json.encode()).hexdigest()
        entry["entry_hash"] = entry_hash

        # Update chain
        self.chain_hash = entry_hash

        # Append to log
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
            f.flush()
            import os
            os.fsync(f.fileno())

        return entry_hash

    def log_recovery_start(self, job_id: str, wallet_id: str,
                           vector: str, confidence: float,
                           biometric_hash: str) -> str:
        """Log recovery operation start."""
        return self.log_event(
            "RECOVERY_START", job_id,
            {"wallet_id": wallet_id, "vector": vector, "confidence": confidence},
            biometric_hash,
        )

    def log_recovery_result(self, job_id: str, success: bool,
                            result_summary: Dict, biometric_hash: str) -> str:
        """Log recovery operation result."""
        return self.log_event(
            "RECOVERY_SUCCESS" if success else "RECOVERY_FAILURE",
            job_id, result_summary, biometric_hash,
        )

    def log_vault_access(self, entry_id: str, action: str,
                         biometric_hash: str) -> str:
        """Log vault access event."""
        return self.log_event(
            f"VAULT_{action.upper()}", entry_id,
            {"vault_entry": entry_id}, biometric_hash,
        )

    def verify_chain(self) -> bool:
        """Verify audit chain integrity."""
        if not self.log_file.exists():
            return True

        prev_hash = "0" * 64
        with open(self.log_file) as f:
            for line in f:
                entry = json.loads(line)
                if entry.get("prev_hash") != prev_hash:
                    return False
                # Recalculate hash
                test_entry = {k: v for k, v in entry.items() if k != "entry_hash"}
                calc_hash = hashlib.sha256(
                    json.dumps(test_entry, sort_keys=True).encode()
                ).hexdigest()
                if calc_hash != entry.get("entry_hash"):
                    return False
                prev_hash = entry["entry_hash"]

        return True


if __name__ == "__main__":
    logger = AuditLogger()
    print("Audit Logger v3.1")
