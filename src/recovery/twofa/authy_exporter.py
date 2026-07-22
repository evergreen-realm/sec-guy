"""
Export TOTP secrets from Authy Desktop.
"""

import json
import os
import platform
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class AuthyExporter:
    @staticmethod
    def get_authy_path() -> Path:
        system = platform.system()
        if system == "Windows":
            return Path(os.environ.get("APPDATA")) / "Authy Desktop" / "Local Storage"
        elif system == "Darwin":
            return Path.home() / "Library" / "Application Support" / "Authy Desktop" / "Local Storage"
        else:
            return Path.home() / ".config" / "Authy Desktop" / "Local Storage"

    @staticmethod
    def export_secrets() -> list:
        """
        Attempt to read Authy's LevelDB and extract secrets.
        Returns list of dicts with 'name', 'secret', 'issuer'.
        """
        authy_path = AuthyExporter.get_authy_path()
        if not authy_path.exists():
            logger.warning("Authy Local Storage directory not found")
            return []

        # This would require leveldb library; fallback to searching for .db files.
        import sqlite3
        db_path = authy_path / "leveldb" / "000003.log"  # may vary
        if not db_path.exists():
            db_path = authy_path / "leveldb" / "CURRENT"
            if not db_path.exists():
                logger.warning("No leveldb found; returning empty")
                return []

        # Simplified: try to read SQLite if it's that format
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM data WHERE key LIKE 'account:%'")
            rows = cursor.fetchall()
            secrets = []
            for key, value in rows:
                # value is JSON with 'authenticator' secret
                try:
                    data = json.loads(value.decode('utf-8'))
                    if 'authenticator' in data:
                        secrets.append({
                            'name': key.split(':')[-1],
                            'secret': data['authenticator']['secret'],
                            'issuer': data.get('issuer', 'Authy')
                        })
                except:
                    continue
            return secrets
        except Exception as e:
            logger.error(f"Failed to parse Authy DB: {e}")
            return []
