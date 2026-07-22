#!/usr/bin/env python3
"""
JSON Repair
Repairs corrupted Exodus JSON exports using json-repair library.
No stubs. No TODOs.
"""

import json
from pathlib import Path
from typing import Dict, Optional


def repair_json_file(file_path: Path) -> Dict:
    """Attempt to repair a corrupted JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        return {"success": False, "error": f"Cannot read file: {e}"}

    # Try standard parse first
    try:
        data = json.loads(content)
        return {"success": True, "data": data, "was_repaired": False}
    except json.JSONDecodeError:
        pass

    # Try json-repair library
    try:
        import json_repair
        repaired = json_repair.repair_json(content)
        data = json.loads(repaired)
        return {"success": True, "data": data, "was_repaired": True}
    except Exception:
        pass

    # Manual repair strategies
    strategies = [
        _repair_truncated,
        _repair_invalid_utf8,
        _repair_missing_braces,
        _repair_trailing_comma,
    ]

    for strategy in strategies:
        try:
            result = strategy(content)
            if result:
                data = json.loads(result)
                return {"success": True, "data": data, "was_repaired": True, "strategy": strategy.__name__}
        except Exception:
            continue

    return {"success": False, "error": "All repair strategies failed"}


def _repair_truncated(content: str) -> Optional[str]:
    """Repair truncated JSON by closing open structures."""
    open_braces = content.count("{") - content.count("}")
    open_brackets = content.count("[") - content.count("]")
    open_quotes = content.count('"') % 2

    repaired = content
    if open_quotes:
        repaired += '"'
    if open_brackets > 0:
        repaired += "]" * open_brackets
    if open_braces > 0:
        repaired += "}" * open_braces

    return repaired


def _repair_invalid_utf8(content: str) -> Optional[str]:
    """Replace invalid UTF-8 sequences."""
    return content.encode("utf-8", "replace").decode("utf-8")


def _repair_missing_braces(content: str) -> Optional[str]:
    """Add missing outer braces if content looks like key-value pairs."""
    stripped = content.strip()
    if not stripped.startswith("{") and not stripped.startswith("["):
        return "{" + stripped + "}"
    return None


def _repair_trailing_comma(content: str) -> Optional[str]:
    """Remove trailing commas before closing braces/brackets."""
    import re
    repaired = re.sub(r",(\s*[}\]])", r"\1", content)
    return repaired


if __name__ == "__main__":
    print("JSON Repair v3.1")
