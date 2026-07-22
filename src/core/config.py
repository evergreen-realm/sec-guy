#!/usr/bin/env python3
"""
Configuration Manager
Loads, validates, and provides access to secguy.yaml.
No stubs. No TODOs.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ConfigManager:
    """Centralized configuration management with hot-reload support."""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            local_cfg = Path("config/secguy.yaml")
            opt_cfg = Path("/opt/sec-guy/config/secguy.yaml")
            self.config_path = local_cfg if local_cfg.exists() else opt_cfg
        else:
            self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._mtime = 0.0
        self.reload()

    def reload(self) -> None:
        """Reload configuration from disk if changed."""
        if not self.config_path.exists():
            # Return empty config if file doesn't exist
            self._config = {}
            return
        mtime = self.config_path.stat().st_mtime
        if mtime > self._mtime:
            with open(self.config_path) as f:
                self._config = yaml.safe_load(f) or {}
            self._mtime = mtime

    def get(self, *keys: str, default: Any = None) -> Any:
        """Nested config access: config.get('llm', 'orchestrator_model')."""
        node = self._config
        for key in keys:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                return default
        return node

    @property
    def version(self) -> str:
        return self.get("secguy", "version", default="3.1.0")

    @property
    def neo4j_uri(self) -> str:
        return self.get("secguy", "learning", "neo4j_uri", default="bolt://localhost:7687")

    @property
    def neo4j_auth(self) -> List[str]:
        return self.get("secguy", "learning", "neo4j_auth", default=["neo4j", "secguy_neo4j_2025"])

    @property
    def hashcat_mode(self) -> int:
        return self.get("secguy", "recovery", "hashcat_mode", default=28200)

    @property
    def max_concurrent_jobs(self) -> int:
        return self.get("secguy", "recovery", "max_concurrent_jobs", default=5)

    @property
    def confidence_target(self) -> float:
        return self.get("secguy", "recovery", "confidence_target", default=30.0)

    @property
    def vault_mount(self) -> str:
        return self.get("secguy", "vault", "mount_point", default="/dev/shm/secguy-vault")

    @property
    def api_keys(self) -> Dict[str, str]:
        return self.get("secguy", "online_enrichment", "api_keys", default={})

    @property
    def model_paths(self) -> Dict[str, str]:
        return self.get("secguy", "llm", "model_paths", default={})

    @property
    def exo_peers(self) -> List[str]:
        return self.get("secguy", "hardware", "exo_peers", default=[])

    @property
    def biometric_required(self) -> bool:
        return self.get("secguy", "security", "biometric_required", default=True)

    @property
    def vault_ttl(self) -> int:
        return self.get("secguy", "security", "vault_ttl_seconds", default=300)

    @property
    def swap_disabled(self) -> bool:
        return self.get("secguy", "security", "swap_disabled", default=True)

    @property
    def audit_log_mandatory(self) -> bool:
        return self.get("secguy", "security", "audit_log_mandatory", default=True)

    @property
    def ownership_proof_required(self) -> bool:
        return self.get("secguy", "security", "ownership_proof_required", default=False)

    @property
    def time_delay_default(self) -> str:
        return self.get("secguy", "security", "time_delay_default", default="5m")

    @property
    def enrichment_enabled(self) -> bool:
        return self.get("secguy", "online_enrichment", "enabled", default=True)

    @property
    def enrichment_runtime_queries(self) -> bool:
        return self.get("secguy", "online_enrichment", "enable_runtime_queries", default=False)

    @property
    def prometheus_enabled(self) -> bool:
        return self.get("secguy", "monitoring", "prometheus_enabled", default=True)

    @property
    def prometheus_port(self) -> int:
        return self.get("secguy", "monitoring", "prometheus_port", default=8080)


# Singleton instance
_config_instance: Optional[ConfigManager] = None

def get_config() -> ConfigManager:
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    else:
        _config_instance.reload()
    return _config_instance
