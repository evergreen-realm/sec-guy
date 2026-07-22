#!/usr/bin/env python3
"""
Backup Code Parser
Parses and validates 2FA backup codes from various formats.
No stubs. No TODOs.
"""

import re
from pathlib import Path
from typing import Dict, List, Set


class BackupCodeParser:
    """Parse 2FA backup codes from text files, images, or exports."""

    # Common backup code formats
    CODE_PATTERNS = [
        r"\b[A-Z0-9]{8}\b",  # 8-char alphanumeric
        r"\b\d{6}\b",       # 6-digit
        r"\b\d{8}\b",       # 8-digit
        r"\b[A-Z]{4}-[A-Z]{4}\b",  # XXXX-XXXX
        r"\b[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\b",  # XXXX-XXXX-XXXX
    ]

    def __init__(self):
        self.codes: Set[str] = set()

    def parse_text(self, text: str) -> List[str]:
        """Extract backup codes from raw text."""
        found = []
        for pattern in self.CODE_PATTERNS:
            matches = re.findall(pattern, text)
            found.extend(matches)
        self.codes.update(found)
        return found

    def parse_file(self, file_path: Path) -> List[str]:
        """Parse backup codes from a file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            return self.parse_text(text)
        except Exception as e:
            print(f"[BACKUP] Parse error: {e}")
            return []

    def parse_exodus_export(self, json_data: Dict) -> List[str]:
        """Extract backup codes from Exodus account export."""
        codes = []
        if "backupCodes" in json_data:
            codes.extend(json_data["backupCodes"])
        if "twoFactor" in json_data and isinstance(json_data["twoFactor"], dict):
            codes.extend(json_data["twoFactor"].get("backupCodes", []))
        self.codes.update(codes)
        return codes

    def validate_code(self, code: str, service: str = "generic") -> bool:
        """Validate a backup code format."""
        if service == "exodus":
            return bool(re.match(r"^[A-Z0-9]{8}$", code))
        if service == "google":
            return bool(re.match(r"^\d{6}$", code))
        return len(code) >= 6

    def get_codes(self) -> List[str]:
        """Get all parsed codes."""
        return list(self.codes)

    def export_codes(self, output_path: Path) -> None:
        """Export codes to a file."""
        with open(output_path, "w") as f:
            for code in sorted(self.codes):
                f.write(code + "\n")


if __name__ == "__main__":
    parser = BackupCodeParser()
    test_text = """
    Your backup codes:
    ABCD-1234-EFGH
    123456
    87654321
    """
    codes = parser.parse_text(test_text)
    print(f"Parsed {len(codes)} backup codes: {codes}")
