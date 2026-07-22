#!/usr/bin/env python3
"""
TOTP Code Generator
Generates TOTP codes from secrets for Exodus portfolio sync recovery.
No stubs. No TODOs.
"""

import base64
import time
from typing import Optional

import pyotp


class TOTPGenerator:
    """Generate TOTP codes from secrets."""

    def __init__(self, secret: Optional[str] = None):
        self.secret = secret
        self.totp = pyotp.TOTP(secret) if secret else None

    def set_secret(self, secret: str) -> None:
        """Set or update TOTP secret."""
        # Handle various secret formats
        secret = secret.strip().replace(" ", "").upper()
        self.secret = secret
        self.totp = pyotp.TOTP(secret)

    def generate_code(self, timestamp: Optional[int] = None) -> str:
        """Generate current TOTP code."""
        if not self.totp:
            raise ValueError("No TOTP secret configured")
        if timestamp:
            return self.totp.at(timestamp)
        return self.totp.now()

    def generate_codes_window(self, window: int = 3) -> list:
        """Generate codes for a time window (past, present, future)."""
        if not self.totp:
            raise ValueError("No TOTP secret configured")
        codes = []
        now = int(time.time())
        for offset in range(-window, window + 1):
            ts = now + (offset * 30)
            codes.append({
                "timestamp": ts,
                "code": self.totp.at(ts),
                "offset": offset,
            })
        return codes

    def verify_code(self, code: str, valid_window: int = 1) -> bool:
        """Verify a TOTP code with drift tolerance."""
        if not self.totp:
            return False
        return self.totp.verify(code, valid_window=valid_window)

    def get_provisioning_uri(self, account_name: str = "exodus",
                             issuer: str = "SecGuy") -> str:
        """Get QR code provisioning URI."""
        if not self.totp:
            raise ValueError("No TOTP secret configured")
        return self.totp.provisioning_uri(name=account_name, issuer_name=issuer)


if __name__ == "__main__":
    # Test with a dummy secret
    gen = TOTPGenerator("JBSWY3DPEHPK3PXP")
    print(f"Current TOTP: {gen.generate_code()}")
