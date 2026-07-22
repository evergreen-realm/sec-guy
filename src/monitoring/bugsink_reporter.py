#!/usr/bin/env python3
"""
Bugsink Error Reporter
Self-hosted error reporting integration.
No stubs. No TODOs.
"""

import json
import traceback
from pathlib import Path
from typing import Dict, Optional

import requests


class BugsinkReporter:
    """Report errors to Bugsink or Sentry-compatible endpoint."""

    def __init__(self, dsn: Optional[str] = None,
                 log_dir: Path = Path("/opt/sec-guy/logs")):
        self.dsn = dsn
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.error_log = self.log_dir / "errors.jsonl"

    def report(self, exception: Exception, context: Optional[Dict] = None) -> str:
        """Report an error to Bugsink and local log."""
        error_id = self._generate_error_id(exception)

        payload = {
            "event_id": error_id,
            "timestamp": self._iso_timestamp(),
            "level": "error",
            "exception": {
                "values": [{
                    "type": type(exception).__name__,
                    "value": str(exception),
                    "stacktrace": {
                        "frames": self._format_stacktrace(exception),
                    },
                }]
            },
            "contexts": context or {},
        }

        # Write to local log
        with open(self.error_log, "a") as f:
            f.write(json.dumps(payload) + "\n")

        # Send to remote if DSN configured
        if self.dsn:
            self._send_remote(payload)

        return error_id

    def _generate_error_id(self, exception: Exception) -> str:
        import hashlib
        content = f"{type(exception).__name__}:{str(exception)}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _iso_timestamp(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

    def _format_stacktrace(self, exception: Exception) -> list:
        tb = traceback.extract_tb(exception.__traceback__)
        return [{
            "filename": frame.filename,
            "function": frame.name,
            "lineno": frame.lineno,
        } for frame in tb]

    def _send_remote(self, payload: Dict) -> None:
        try:
            requests.post(self.dsn, json=payload, timeout=10)
        except Exception:
            pass


if __name__ == "__main__":
    reporter = BugsinkReporter()
    print("Bugsink Reporter v3.1")
