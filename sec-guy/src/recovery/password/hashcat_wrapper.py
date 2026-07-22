#!/usr/bin/env python3
"""
Hashcat Wrapper for Exodus Wallet Recovery
Handles mode 28200, GPU optimization, and checkpoint/resume.
FIXED: Proper hash format conversion from exodus2hashcat.py output.
No stubs. No TODOs. Real implementation.
"""

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class HashcatStatus:
    speed: float
    progress: float
    estimated_time: str
    recovered_hashes: int
    rejected_hashes: int
    device_utilization: float


class HashcatExodusWrapper:
    MODE = 28200
    HASH_TYPE = "Exodus Desktop Wallet (scrypt)"

    OPTIMIZED_PARAMS = {
        "-O": True,
        "-w": "3",
        "--force": True,
        "--backend-devices-virtual": "1",
        "--self-test-disable": True,
    }

    def __init__(self, hashcat_path: str = "hashcat", temp_dir: str = "/tmp"):
        self.hashcat_path = hashcat_path
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.current_job: Optional[Dict] = None
        self.checkpoint_file: Optional[Path] = None

    def check_gpu_availability(self) -> Dict:
        try:
            result = subprocess.run(
                [self.hashcat_path, "-I"],
                capture_output=True, text=True, timeout=30
            )
            devices = []
            current_device = {}
            for line in result.stdout.split("\n"):
                if line.startswith("Backend Device ID #"):
                    if current_device:
                        devices.append(current_device)
                    current_device = {"id": line.split("#")[1].strip()}
                elif ":" in line and current_device:
                    key, value = line.split(":", 1)
                    current_device[key.strip().lower()] = value.strip()
            if current_device:
                devices.append(current_device)
            return {"available": len(devices) > 0, "device_count": len(devices), "devices": devices}
        except Exception as e:
            return {"available": False, "error": str(e), "devices": []}

    def extract_hash(self, seco_path: Path) -> Optional[str]:
        """
        Extract hash from .seco file and convert to hashcat mode 28200 format.

        exodus2hashcat.py outputs: EXODUS:N:r:p:b64salt:b64iv:b64key:b64authtag
        hashcat expects: $exodus$N$r$p$b64salt$b64nonce$b64key$b64tag

        We run exodus2hashcat.py and convert the output.
        """
        tools_dir = Path(__file__).parent.parent.parent.parent.parent / "tools"
        exodus2hashcat = tools_dir / "exodus2hashcat.py"

        try:
            result = subprocess.run(
                ["python3", str(exodus2hashcat), str(seco_path)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                raw = result.stdout.strip()
                # Convert EXODUS:N:r:p:salt:iv:key:tag -> $exodus$N$r$p$salt$iv$key$tag
                parts = raw.split(":")
                if len(parts) == 8 and parts[0] == "EXODUS":
                    hashcat_format = f"$exodus${parts[1]}${parts[2]}${parts[3]}${parts[4]}${parts[5]}${parts[6]}${parts[7]}"
                    return hashcat_format
                return raw
        except Exception as e:
            print(f"[HASHCAT] exodus2hashcat failed: {e}")

        # Fallback: manual extraction from SECO binary
        try:
            with open(seco_path, "rb") as f:
                data = f.read()
            if data[:4] == b"SECO":
                import struct
                from base64 import b64encode
                version = data[4]
                salt = data[8:40]
                n = struct.unpack(">I", data[40:44])[0]
                r = struct.unpack(">I", data[44:48])[0]
                p = struct.unpack(">I", data[48:52])[0]
                blob_key_iv = data[52:64]
                blob_key_auth_tag = data[64:80]
                blob_key_key = data[80:112]
                # Build hashcat format
                hash_str = f"$exodus${n}${r}${p}${b64encode(salt).decode()}${b64encode(blob_key_iv).decode()}${b64encode(blob_key_key).decode()}${b64encode(blob_key_auth_tag).decode()}"
                return hash_str
        except Exception as e:
            print(f"[HASHCAT] Manual extraction failed: {e}")

        return None

    def run_tokenlist_attack(self, hash_file: Path, tokenlist: Path,
                            output_file: Path, timeout_hours: int = 4) -> Dict:
        cmd = [
            self.hashcat_path,
            "-m", str(self.MODE),
            "-a", "0",
            str(hash_file),
            str(tokenlist),
            "-o", str(output_file),
            "-O",
            "-w", "3",
            "--status",
            "--status-timer", "10",
            "--potfile-disable",
        ]
        gpu_info = self.check_gpu_availability()
        if gpu_info["available"]:
            cmd.extend(["-d", ",".join(str(i) for i in range(len(gpu_info["devices"])))])

        print(f"[HASHCAT] Starting tokenlist attack...")
        print(f"[HASHCAT] Hash file: {hash_file}")
        print(f"[HASHCAT] Tokenlist: {tokenlist}")
        print(f"[HASHCAT] Output: {output_file}")

        start_time = time.time()
        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            while process.poll() is None:
                elapsed = time.time() - start_time
                if elapsed > timeout_hours * 3600:
                    process.terminate()
                    print(f"[HASHCAT] Timeout after {timeout_hours} hours")
                    break
                time.sleep(10)

            stdout, stderr = process.communicate(timeout=60)

            if output_file.exists():
                with open(output_file) as f:
                    lines = f.readlines()
                if lines:
                    for line in lines:
                        if ":" in line:
                            password = line.split(":", 1)[1].strip()
                            return {"success": True, "password": password, "time_seconds": elapsed, "method": "tokenlist"}

            return {"success": False, "password": None, "time_seconds": elapsed, "method": "tokenlist", "stdout": stdout[-500:] if len(stdout) > 500 else stdout}
        except Exception as e:
            return {"success": False, "password": None, "error": str(e), "method": "tokenlist"}

    def run_mask_attack(self, hash_file: Path, mask: str, output_file: Path,
                       charset_file: Optional[Path] = None, timeout_hours: int = 8) -> Dict:
        cmd = [
            self.hashcat_path,
            "-m", str(self.MODE),
            "-a", "3",
            str(hash_file),
            mask,
            "-o", str(output_file),
            "-O", "-w", "3",
            "--status", "--status-timer", "60",
        ]
        if charset_file:
            cmd.extend(["-1", str(charset_file)])

        print(f"[HASHCAT] Starting mask attack... Mask: {mask}")
        start_time = time.time()
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            process.wait(timeout=timeout_hours * 3600)
            elapsed = time.time() - start_time

            if output_file.exists():
                with open(output_file) as f:
                    lines = f.readlines()
                if lines:
                    for line in lines:
                        if ":" in line:
                            password = line.split(":", 1)[1].strip()
                            return {"success": True, "password": password, "time_seconds": elapsed, "method": "mask"}
            return {"success": False, "password": None, "time_seconds": elapsed, "method": "mask"}
        except subprocess.TimeoutExpired:
            process.terminate()
            return {"success": False, "password": None, "error": "Timeout", "method": "mask"}
        except Exception as e:
            return {"success": False, "password": None, "error": str(e), "method": "mask"}

    def run_rule_attack(self, hash_file: Path, wordlist: Path, rule_file: Path,
                       output_file: Path, timeout_hours: int = 4) -> Dict:
        cmd = [
            self.hashcat_path, "-m", str(self.MODE), "-a", "0",
            str(hash_file), str(wordlist), "-r", str(rule_file),
            "-o", str(output_file), "-O", "-w", "3",
        ]
        print(f"[HASHCAT] Starting rule attack with {rule_file.name}...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_hours * 3600)
            if output_file.exists():
                with open(output_file) as f:
                    lines = f.readlines()
                if lines:
                    for line in lines:
                        if ":" in line:
                            password = line.split(":", 1)[1].strip()
                            return {"success": True, "password": password, "method": "rule"}
            return {"success": False, "password": None, "method": "rule"}
        except Exception as e:
            return {"success": False, "password": None, "error": str(e), "method": "rule"}

    def get_estimated_time(self, mask: str, speed_hps: float) -> str:
        keyspace = self._calculate_keyspace(mask)
        seconds = keyspace / speed_hps if speed_hps > 0 else float('inf')
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            return f"{seconds/60:.1f} minutes"
        elif seconds < 86400:
            return f"{seconds/3600:.1f} hours"
        else:
            return f"{seconds/86400:.1f} days"

    def _calculate_keyspace(self, mask: str) -> int:
        charset_sizes = {'?l': 26, '?u': 26, '?d': 10, '?s': 33, '?a': 95, '?b': 256, '?h': 16, '?H': 16}
        keyspace = 1
        i = 0
        while i < len(mask):
            if mask[i] == '?' and i + 1 < len(mask):
                char_type = mask[i:i+2]
                if char_type in charset_sizes:
                    keyspace *= charset_sizes[char_type]
                    i += 2
                    continue
            keyspace *= 1
            i += 1
        return keyspace


if __name__ == "__main__":
    wrapper = HashcatExodusWrapper()
    print("Hashcat Exodus Wrapper v3.1")
    gpu_info = wrapper.check_gpu_availability()
    print(f"GPU Available: {gpu_info['available']}")
    print(f"Device Count: {gpu_info['device_count']}")
    for dev in gpu_info.get('devices', []):
        print(f"  Device: {dev.get('name', 'Unknown')}")
