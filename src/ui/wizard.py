"""
Setup wizard – interactive configuration of SEC-GUY.
"""

from pathlib import Path
import yaml
import logging
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from ..core.platform import Platform

logger = logging.getLogger(__name__)
console = Console()


class SetupWizard:
    def __init__(self, config_path: Path = None):
        self.config_path = config_path or Platform.get_config_dir() / "secguy.yaml"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def run(self) -> None:
        console.print(Panel("SEC-GUY Setup Wizard", style="bold blue"))
        console.print("This will create a configuration file for your data recovery framework.\n")

        config = {}

        # Hashcat
        config["hashcat_bin"] = Prompt.ask("Path to hashcat binary", default="hashcat")
        config["hashcat_timeout"] = int(Prompt.ask("Hashcat timeout (seconds)", default="86400"))

        # BTCRecover
        btcr_path = Prompt.ask("Path to BTCRecover directory", default="tools/btcrecover")
        config["btcrecover_path"] = str(Path(btcr_path).resolve())

        # LLM settings
        config["llm"] = {
            "local_enabled": Confirm.ask("Enable local LLM (LM Studio)?", default=True),
            "cloud_enabled": Confirm.ask("Enable cloud LLM providers?", default=True),
            "default_cloud": Prompt.ask("Default cloud provider", default="groq"),
            "lmstudio_url": Prompt.ask("LM Studio API URL", default="http://localhost:1234/v1"),
            "exo_enabled": Confirm.ask("Enable EXO distributed inference?", default=False),
        }

        # API keys
        config["api_keys"] = {}
        if Confirm.ask("Enter Groq API key?", default=False):
            config["api_keys"]["GROQ_API_KEY"] = Prompt.ask("Groq API key", password=True)
        if Confirm.ask("Enter Cerebras API key?", default=False):
            config["api_keys"]["CEREBRAS_API_KEY"] = Prompt.ask("Cerebras API key", password=True)

        # Neo4j
        config["neo4j"] = {
            "uri": Prompt.ask("Neo4j URI", default="bolt://localhost:7687"),
            "user": Prompt.ask("Neo4j user", default="neo4j"),
            "password": Prompt.ask("Neo4j password", password=True, default="secguy_neo4j_2025"),
        }

        # Write config
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        console.print(f"[green]Configuration saved to {self.config_path}[/]")
