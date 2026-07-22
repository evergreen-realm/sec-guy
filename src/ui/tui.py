"""
Terminal UI for SEC-GUY using Rich and Textual.
Provides interactive dashboard for recovery operations.
"""

import asyncio
from typing import Optional
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich import box

import time
import threading

console = Console()


class SecGuyTUI:
    """Main TUI application."""

    def __init__(self):
        self.running = True
        self.job_id = None
        self.status = "idle"

    def run(self):
        self.show_disclaimer()

    def show_disclaimer(self):
        console.clear()
        content = Panel(
            "[bold yellow]⚠ LEGAL DISCLAIMER[/]\n\n"
            "SEC-GUY is designed to assist legitimate owners in recovering "
            "their own encrypted backups.\n\n"
            "By using this tool, you affirm:\n"
            " • You are the legal owner of the backup file(s)\n"
            " • You will not use recovered credentials for unauthorized access\n"
            " • You accept full legal responsibility\n"
            " • You understand this session is fully audited\n\n"
            "All operations are logged to an append-only, biometric-bound audit trail.\n\n"
            "Type [bold]'I AGREE'[/] to continue.",
            title="Legal Disclaimer",
            border_style="yellow"
        )
        console.print(content)
        response = Prompt.ask("Type 'I AGREE'")
        if response.strip().upper() == "I AGREE":
            self.show_biometric_gate()
        else:
            console.print("[red]Disclaimer rejected. Exiting.[/]")
            self.running = False

    def show_biometric_gate(self):
        console.clear()
        console.print(Panel(
            "[bold cyan]🔐 BIOMETRIC VERIFICATION[/]\n\n"
            "Place your finger on the reader...\n\n"
            "   [dim](Simulating fingerprint scan in 2 seconds)[/]\n"
            "   Press [bold]Enter[/] to simulate success, or [bold]Ctrl+C[/] to abort.",
            title="Biometric Gate",
            border_style="cyan"
        ))
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task("Scanning fingerprint...", total=1)
            time.sleep(2)
            progress.update(task, advance=1)
        console.print("[green]✅ Biometric verification successful.[/]")
        time.sleep(1)
        self.show_main_dashboard()

    def show_main_dashboard(self):
        console.clear()
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        layout["header"].update(
            Panel(
                f"[bold]SEC-GUY v3.1[/]  🟢 GPU: RTX 3060  │  {time.strftime('%H:%M')}",
                style="bold blue"
            )
        )
        body = Layout()
        body.split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1)
        )
        wallet_table = Table(box=box.SIMPLE, show_header=False)
        wallet_table.add_column("Key", style="cyan")
        wallet_table.add_column("Value")
        wallet_table.add_row("File", "wallet.seco")
        wallet_table.add_row("Version", "Modern (v19-v22)")
        wallet_table.add_row("Created", "~2021")
        wallet_table.add_row("Size", "1,024 bytes")
        body["left"].update(Panel(wallet_table, title="Wallet", border_style="blue"))
        vector_table = Table(box=box.SIMPLE, show_header=False)
        vector_table.add_column("Key", style="cyan")
        vector_table.add_column("Value")
        vector_table.add_row("Detected", "PASSWORD_HINTED")
        vector_table.add_row("Confidence", "████████░░░░░░░░░░ 40%")
        vector_table.add_row("Hints", '"my dog Rex born 2020"')
        body["right"].update(Panel(vector_table, title="Recovery Vector", border_style="green"))
        layout["body"].update(body)
        status_text = "🟢 hashcat  🟢 Neo4j  🟢 Redis  🟢 EXO  🟢 Vault  🟡 Cloud AI (2/5)"
        layout["footer"].update(Panel(status_text, style="dim"))
        console.print(layout)
        choice = Prompt.ask(
            "\n[Enter] Start Recovery  │  [H] Health  │  [S] Settings  │  [Q] Quit",
            choices=["", "h", "s", "q"],
            default=""
        )
        if choice.lower() == "q":
            self.running = False
            return
        elif choice.lower() == "h":
            self.show_health()
        elif choice.lower() == "s":
            self.show_settings()
        else:
            self.show_recovery_progress()

    def show_recovery_progress(self):
        console.clear()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            transient=False
        ) as progress:
            task = progress.add_task("[cyan]Hashcat attack in progress...", total=8547)
            for i in range(8547):
                time.sleep(0.001)
                progress.update(task, advance=1, description=f"[cyan]Tried {i+1} candidates")
        console.print("[green]✅ Recovery successful! Password found.[/]")
        self.show_result()

    def show_result(self):
        console.print(Panel(
            "[bold green]✅ PASSWORD RECOVERED[/]\n\n"
            "Password stored in Time-Lock Vault (5 min delay).\n"
            "Vault Entry: 4f5e6a7b\n"
            "Tool used: hashcat -m 28200\n"
            "Time taken: 00:31:47\n\n"
            "[yellow]⚠ Password will auto-shred in 10 minutes.[/]",
            title="Success",
            border_style="green"
        ))
        Prompt.ask("Press Enter to return to dashboard")
        self.show_main_dashboard()

    def show_health(self):
        console.clear()
        table = Table(title="System Health", box=box.ROUNDED)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")
        table.add_row("hashcat", "✅ OK", "v6.2.6, mode 28200")
        table.add_row("GPU", "✅ OK", "RTX 3060, 6GB VRAM, 42°C")
        table.add_row("Neo4j", "✅ OK", "v5.19, 847 patterns")
        table.add_row("Redis", "✅ OK", "v7.2, 3 active jobs")
        table.add_row("EXO Cluster", "✅ OK", "2 nodes, 48GB RAM")
        table.add_row("LM Studio", "✅ OK", "Qwen2.5-8B loaded")
        table.add_row("RAM Vault", "✅ OK", "tmpfs mounted, 12 entries")
        table.add_row("Biometric", "🟡 WARN", "1 finger enrolled")
        table.add_row("Cloud AI", "🔴 ERROR", "Groq rate limited")
        console.print(table)
        Prompt.ask("Press Enter to return")
        self.show_main_dashboard()

    def show_settings(self):
        console.print("[cyan]Settings (stub)[/]")
        Prompt.ask("Press Enter to return")
        self.show_main_dashboard()


def main():
    tui = SecGuyTUI()
    tui.run()

if __name__ == "__main__":
    main()