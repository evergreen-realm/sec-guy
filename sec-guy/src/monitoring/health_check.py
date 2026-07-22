#!/usr/bin/env python3
"""
Health Check
System health monitoring for Sec Guy components.
No stubs. No TODOs.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import psutil


@dataclass
class HealthStatus:
    component: str
    healthy: bool
    details: Dict
    error: Optional[str] = None


class HealthChecker:
    """Check health of all Sec Guy components."""

    def __init__(self):
        self.checks: Dict[str, callable] = {
            "redis": self._check_redis,
            "neo4j": self._check_neo4j,
            "gpu": self._check_gpu,
            "hashcat": self._check_hashcat,
            "exo": self._check_exo,
            "vault": self._check_vault,
            "biometric": self._check_biometric,
        }

    def check_all(self) -> List[HealthStatus]:
        """Run all health checks."""
        results = []
        for name, check_fn in self.checks.items():
            try:
                status = check_fn()
                results.append(status)
            except Exception as e:
                results.append(HealthStatus(
                    component=name, healthy=False, details={}, error=str(e)
                ))
        return results

    def _check_redis(self) -> HealthStatus:
        try:
            import redis
            r = redis.Redis(host="localhost", port=6379, socket_connect_timeout=2)
            r.ping()
            return HealthStatus("redis", True, {"version": r.info().get("redis_version", "unknown")})
        except Exception as e:
            return HealthStatus("redis", False, {}, str(e))

    def _check_neo4j(self) -> HealthStatus:
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver("bolt://localhost:7687",
                                          auth=("neo4j", "secguy_neo4j_2025"))
            with driver.session() as session:
                result = session.run("RETURN 1 AS test")
                record = result.single()
            driver.close()
            return HealthStatus("neo4j", True, {"connected": True})
        except Exception as e:
            return HealthStatus("neo4j", False, {}, str(e))

    def _check_gpu(self) -> HealthStatus:
        try:
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.split("\n")
                return HealthStatus("gpu", True, {"nvidia_smi": "available"})
            return HealthStatus("gpu", False, {}, "nvidia-smi failed")
        except Exception as e:
            return HealthStatus("gpu", False, {}, str(e))

    def _check_hashcat(self) -> HealthStatus:
        try:
            result = subprocess.run(["hashcat", "-I"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return HealthStatus("hashcat", True, {"devices_found": True})
            return HealthStatus("hashcat", False, {}, "No devices found")
        except Exception as e:
            return HealthStatus("hashcat", False, {}, str(e))

    def _check_exo(self) -> HealthStatus:
        try:
            import requests
            resp = requests.get("http://localhost:52415/v1/health", timeout=5)
            if resp.status_code == 200:
                return HealthStatus("exo", True, {"healthy": True})
            return HealthStatus("exo", False, {}, f"HTTP {resp.status_code}")
        except Exception as e:
            return HealthStatus("exo", False, {}, str(e))

    def _check_vault(self) -> HealthStatus:
        vault_path = Path("/dev/shm/secguy-vault")
        if vault_path.exists():
            stat = vault_path.stat()
            return HealthStatus("vault", True, {
                "mounted": True,
                "size_mb": stat.st_size / (1024 * 1024),
            })
        return HealthStatus("vault", False, {}, "Vault not mounted")

    def _check_biometric(self) -> HealthStatus:
        try:
            result = subprocess.run(["fprintd-list", "secguy"],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return HealthStatus("biometric", True, {"enrolled": True})
            return HealthStatus("biometric", False, {}, "No enrolled fingerprints")
        except Exception as e:
            return HealthStatus("biometric", False, {}, str(e))

    def get_system_stats(self) -> Dict:
        """Get general system statistics."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_mb": psutil.virtual_memory().available // (1024 * 1024),
            "disk_usage_percent": psutil.disk_usage("/").percent,
            "swap_used_mb": psutil.swap_memory().used // (1024 * 1024),
        }


if __name__ == "__main__":
    checker = HealthChecker()
    for status in checker.check_all():
        print(f"{status.component}: {'OK' if status.healthy else 'FAIL'} - {status.error or ''}")
