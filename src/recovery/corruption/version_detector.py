"""
Exodus wallet version and parameter detection.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Known magic bytes for Exodus wallet versions
WALLET_MAGIC_BYTES = {
    b'SECO': 'modern',      # v19+
    b'EXOD': 'legacy',      # older versions
    b'EXODUS': 'ancient',   # very old
}

EXODUS_VERSION_MAP = {
    'modern': {'scrypt_n': 16384, 'scrypt_r': 8, 'scrypt_p': 1, 'version_range': 'v19-v25+'},
    'legacy': {'scrypt_n': 8192, 'scrypt_r': 8, 'scrypt_p': 1, 'version_range': 'v1-v18'},
    'ancient': {'scrypt_n': 4096, 'scrypt_r': 8, 'scrypt_p': 1, 'version_range': 'v0-v1'},
}


class ExodusVersionDetector:
    """
    Detects Exodus wallet version and extracts scrypt parameters from .seco file.
    """

    def __init__(self, wallet_path: Optional[Path] = None):
        self.wallet_path = wallet_path
        self._info = None

    def detect(self) -> Dict[str, Any]:
        """
        Return a dictionary with detected version, scrypt params, and metadata.
        """
        if self._info is None:
            self._parse_wallet()
        return self._info

    def detect_from_seco(self, wallet_path: Path) -> Dict[str, Any]:
        """Detect version era and parameters from a .seco wallet file."""
        self.wallet_path = wallet_path
        self._info = None
        return self.detect()

    def _parse_wallet(self) -> None:
        """Read the wallet header and populate info."""
        if not self.wallet_path or not self.wallet_path.exists():
            self._info = {'valid': False, 'error': 'File not found or not specified'}
            return

        try:
            with open(self.wallet_path, 'rb') as f:
                header = f.read(16)  # read first 16 bytes
            if len(header) < 4:
                self._info = {'valid': False, 'error': 'Header too short'}
                return

            magic = header[:4]
            if magic in WALLET_MAGIC_BYTES:
                era = WALLET_MAGIC_BYTES[magic]
                params = EXODUS_VERSION_MAP[era]
                self._info = {
                    'valid': True,
                    'version_era': era,
                    'scrypt_n': params['scrypt_n'],
                    'scrypt_r': params['scrypt_r'],
                    'scrypt_p': params['scrypt_p'],
                    'version_range': params['version_range'],
                    'magic_bytes': magic.hex(),
                }
            else:
                self._info = {'valid': False, 'error': 'Unknown magic bytes'}

        except Exception as e:
            logger.exception("Failed to parse wallet header")
            self._info = {'valid': False, 'error': str(e)}

    def is_valid(self) -> bool:
        """Return True if the file appears to be a valid Exodus wallet."""
        return self.detect().get('valid', False)


def parse_wallet_header(wallet_path: Path) -> Dict[str, Any]:
    """
    Convenience function to parse wallet header and return scrypt parameters.
    """
    detector = ExodusVersionDetector(wallet_path)
    info = detector.detect()
    if info.get('valid'):
        return {
            'n': info['scrypt_n'],
            'r': info['scrypt_r'],
            'p': info['scrypt_p'],
            'version': info['version_era']
        }
    raise ValueError(f"Invalid wallet file: {wallet_path}")


def detect_exodus_version(wallet_path: Path) -> Optional[str]:
    """Return the version era string, or None if invalid."""
    info = ExodusVersionDetector(wallet_path).detect()
    return info.get('version_era') if info.get('valid') else None


def extract_scrypt_params(wallet_path: Path) -> Tuple[int, int, int]:
    """Return (N, r, p) for scrypt."""
    info = ExodusVersionDetector(wallet_path).detect()
    if info.get('valid'):
        return (info['scrypt_n'], info['scrypt_r'], info['scrypt_p'])
    raise ValueError("Cannot extract scrypt params from invalid wallet")
