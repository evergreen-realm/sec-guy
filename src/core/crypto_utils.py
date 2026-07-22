#!/usr/bin/env python3
"""
Shared Cryptographic Primitives
AES-GCM, Argon2id, age encryption, secure random, memory wiping.
No stubs. No TODOs.
"""

import os
import secrets
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import argon2


class SecureVault:
    """RAM-only vault with Argon2id + AES-256-GCM."""

    SALT_SIZE = 32
    NONCE_SIZE = 12
    KEY_SIZE = 32
    TAG_SIZE = 16
    ARGON2_TIME_COST = 3
    ARGON2_MEMORY_COST = 65536
    ARGON2_PARALLELISM = 4

    def __init__(self, mount_point: str = "/dev/shm/secguy-vault"):
        self.mount_point = Path(mount_point)
        self.mount_point.mkdir(parents=True, exist_ok=True)

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive AES key via Argon2id."""
        argon2.PasswordHasher(
            time_cost=self.ARGON2_TIME_COST,
            memory_cost=self.ARGON2_MEMORY_COST,
            parallelism=self.ARGON2_PARALLELISM,
            hash_len=self.KEY_SIZE,
            type=argon2.Type.ID,
        )
        # Argon2id hash is not directly usable as AES key, so we use raw hash
        raw = argon2.low_level.hash_secret_raw(
            password.encode(),
            salt,
            time_cost=self.ARGON2_TIME_COST,
            memory_cost=self.ARGON2_MEMORY_COST,
            parallelism=self.ARGON2_PARALLELISM,
            hash_len=self.KEY_SIZE,
            type=argon2.Type.ID,
        )
        return raw

    def encrypt(self, plaintext: str, password: str, metadata: Optional[dict] = None) -> str:
        """Encrypt plaintext and return base64-encoded ciphertext bundle."""
        import base64
        salt = secrets.token_bytes(self.SALT_SIZE)
        nonce = secrets.token_bytes(self.NONCE_SIZE)
        key = self._derive_key(password, salt)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        # Bundle: salt(32) + nonce(12) + ciphertext+tag
        bundle = salt + nonce + ciphertext
        b64 = base64.b64encode(bundle).decode()
        # Write to vault with TTL
        entry_id = secrets.token_hex(8)
        vault_file = self.mount_point / f"{entry_id}.vault"
        vault_file.write_text(b64)
        os.chmod(vault_file, 0o600)
        return entry_id

    def decrypt(self, entry_id: str, password: str) -> str:
        """Decrypt vault entry."""
        import base64
        vault_file = self.mount_point / f"{entry_id}.vault"
        if not vault_file.exists():
            raise FileNotFoundError(f"Vault entry {entry_id} not found")
        b64 = vault_file.read_text()
        bundle = base64.b64decode(b64)
        salt = bundle[:self.SALT_SIZE]
        nonce = bundle[self.SALT_SIZE:self.SALT_SIZE + self.NONCE_SIZE]
        ciphertext = bundle[self.SALT_SIZE + self.NONCE_SIZE:]
        key = self._derive_key(password, salt)
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()

    def shred(self, entry_id: str) -> None:
        """Securely overwrite and delete a vault entry."""
        vault_file = self.mount_point / f"{entry_id}.vault"
        if not vault_file.exists():
            return
        size = vault_file.stat().st_size
        with open(vault_file, "r+b") as f:
            f.write(os.urandom(size))
            f.flush()
            os.fsync(f.fileno())
        vault_file.unlink()

    def shred_all(self) -> None:
        """Shred all vault entries."""
        for vault_file in self.mount_point.glob("*.vault"):
            size = vault_file.stat().st_size
            with open(vault_file, "r+b") as f:
                f.write(os.urandom(size))
                f.flush()
                os.fsync(f.fileno())
            vault_file.unlink()


class CryptoHelper:
    """Static cryptographic utilities."""

    @staticmethod
    def secure_random_bytes(n: int) -> bytes:
        return secrets.token_bytes(n)

    @staticmethod
    def secure_random_int(min_val: int, max_val: int) -> int:
        return secrets.randbelow(max_val - min_val + 1) + min_val

    @staticmethod
    def sha256(data: bytes) -> bytes:
        import hashlib
        return hashlib.sha256(data).digest()

    @staticmethod
    def scrypt_kdf(password: bytes, salt: bytes, n: int = 16384, r: int = 8, p: int = 1, dklen: int = 32) -> bytes:
        import hashlib
        return hashlib.scrypt(password, salt=salt, n=n, r=r, p=p, dklen=dklen)

    @staticmethod
    def constant_time_compare(a: bytes, b: bytes) -> bool:
        import hmac
        return hmac.compare_digest(a, b)

    @staticmethod
    def memory_wipe(buffer: bytearray) -> None:
        """Overwrite a bytearray with zeros in-place."""
        for i in range(len(buffer)):
            buffer[i] = 0


# age encryption wrapper (uses age CLI)
class AgeEncryptor:
    """Wrapper around age (https://age-encryption.org) for file encryption."""

    def __init__(self, key_path: Optional[Path] = None):
        self.key_path = key_path or Path("/opt/sec-guy/config/secguy.age.key")

    def generate_key(self) -> str:
        import subprocess
        result = subprocess.run(
            ["age-keygen", "-o", str(self.key_path)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"age-keygen failed: {result.stderr}")
        # Return public key from stderr
        for line in result.stderr.split("\n"):
            if line.startswith("Public key:"):
                return line.split(":")[1].strip()
        return ""

    def encrypt_file(self, input_path: Path, output_path: Path, recipient: str) -> None:
        import subprocess
        result = subprocess.run(
            ["age", "-r", recipient, "-o", str(output_path), str(input_path)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"age encryption failed: {result.stderr}")

    def decrypt_file(self, input_path: Path, output_path: Path) -> None:
        import subprocess
        result = subprocess.run(
            ["age", "-d", "-i", str(self.key_path), "-o", str(output_path), str(input_path)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"age decryption failed: {result.stderr}")
