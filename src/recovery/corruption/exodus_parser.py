"""
Alias module for Exodus wallet header parsing.
Redirects to version_detector for backward compatibility.
"""

from .version_detector import (
    ExodusVersionDetector,
    parse_wallet_header,
    detect_exodus_version,
    extract_scrypt_params,
    WALLET_MAGIC_BYTES,
    EXODUS_VERSION_MAP
)

__all__ = [
    'ExodusVersionDetector',
    'parse_wallet_header',
    'detect_exodus_version',
    'extract_scrypt_params',
    'WALLET_MAGIC_BYTES',
    'EXODUS_VERSION_MAP'
]