#!/usr/bin/env python3
"""
Setup Wizard
Interactive terminal wizard for first-time configuration.
No stubs. No TODOs.
"""

from pathlib import Path
from typing import Dict


class SetupWizard:
    """Interactive setup wizard for Sec Guy."""

    def __init__(self):
        self.config: Dict = {}

    def run(self) -> Dict:
        """Run the full setup wizard."""
        print("=" * 60)
        print("SEC-GUY v3.1 Setup Wizard")
        print("=" * 60)
        print()

        self._configure_hardware()
        self._configure_llm()
        self._configure_security()
        self._configure_enrichment()
        self._configure_monitoring()

        self._save_config()

        print()
        print("Setup complete! Configuration saved to config/secguy.yaml.")
        return self.config

    def _save_config(self, path: Path = Path("config/secguy.yaml")) -> None:
        """Write current configuration dictionary to secguy.yaml."""
        import yaml
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def _configure_hardware(self) -> None:
        print("--- Hardware Configuration ---")
        machine = input("Machine type [t490/production]: ").strip().lower() or "t490"
        self.config["hardware"] = {"primary_machine": machine}

    def _configure_llm(self) -> None:
        print("--- LLM Configuration ---")
        exo = input("Enable EXO cluster? [Y/n]: ").strip().lower() != "n"
        self.config["llm"] = {"exo_cluster": exo}

    def _configure_security(self) -> None:
        print("--- Security Configuration ---")
        bio = input("Require biometric authentication? [Y/n]: ").strip().lower() != "n"
        delay = input("Time delay (e.g., 5m, 1h): ").strip() or "5m"
        self.config["security"] = {
            "biometric_required": bio,
            "time_delay_default": delay,
        }

    def _configure_enrichment(self) -> None:
        print("--- Online Enrichment ---")
        enabled = input("Enable online enrichment? [Y/n]: ").strip().lower() != "n"
        self.config["online_enrichment"] = {"enabled": enabled}

    def _configure_monitoring(self) -> None:
        print("--- Monitoring ---")
        prom = input("Enable Prometheus metrics? [Y/n]: ").strip().lower() != "n"
        self.config["monitoring"] = {"prometheus_enabled": prom}


if __name__ == "__main__":
    wizard = SetupWizard()
    config = wizard.run()
