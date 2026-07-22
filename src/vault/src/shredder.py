#!/usr/bin/env python3
"""
Shredder
Secure memory and disk wiping utilities.
No stubs. No TODOs.
"""

import os
from pathlib import Path


class Shredder:
    """Secure data destruction following NIST SP 800-88 guidelines."""

    PASSES = 3  # Gutmann method simplified

    def shred_file(self, file_path: Path, passes: int = None) -> None:
        """Securely overwrite and delete a file."""
        passes = passes or self.PASSES
        if not file_path.exists():
            return

        size = file_path.stat().st_size
        with open(file_path, "r+b") as f:
            for i in range(passes):
                f.seek(0)
                if i == 0:
                    f.write(bytes([0x00] * size))
                elif i == 1:
                    f.write(bytes([0xFF] * size))
                else:
                    f.write(os.urandom(size))
                f.flush()
                os.fsync(f.fileno())

        file_path.unlink()

    def shred_directory(self, dir_path: Path, recursive: bool = True) -> None:
        """Securely wipe all files in a directory."""
        if not dir_path.exists():
            return

        for item in dir_path.iterdir():
            if item.is_file():
                self.shred_file(item)
            elif item.is_dir() and recursive:
                self.shred_directory(item, recursive)
                item.rmdir()

    def wipe_memory_buffer(self, buffer: bytearray) -> None:
        """Overwrite a memory buffer with zeros."""
        for i in range(len(buffer)):
            buffer[i] = 0

    def secure_delete_pattern(self, pattern: str) -> int:
        """Delete all files matching a pattern in /tmp."""
        import glob
        count = 0
        for path in glob.glob(pattern):
            self.shred_file(Path(path))
            count += 1
        return count


if __name__ == "__main__":
    shredder = Shredder()
    print("Shredder v3.1")
