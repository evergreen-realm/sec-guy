#!/usr/bin/env python3
"""
Sec Guy Main Entry Point
CLI interface for wallet recovery operations.
No stubs. No TODOs.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.orchestrator import SecGuyOrchestrator, RecoveryVector
from src.core.config import get_config
from src.guardian.src.biometric_gate import BiometricGate
from src.guardian.src.legal_disclaimer import LegalDisclaimer
from src.monitoring.health_check import HealthChecker


def main():
    parser = argparse.ArgumentParser(
        description="SEC-GUY v3.1 — Exodus Wallet Recovery Agent"
    )
    parser.add_argument("--wallet", "-w", type=Path, required=True,
                        help="Path to Exodus wallet file (.seco)")
    parser.add_argument("--hints", "-H", type=str, default="",
                        help="User hints for password recovery")
    parser.add_argument("--seed", "-s", type=str, default="",
                        help="Partial seed phrase (space-separated, use ? for missing words)")
    parser.add_argument("--vector", "-v", type=str, default="auto",
                        choices=["auto", "password", "seed", "corruption", "2fa"],
                        help="Recovery vector (auto-detect if not specified)")
    parser.add_argument("--timeout", "-t", type=int, default=240,
                        help="Timeout in minutes (default: 240)")
    parser.add_argument("--tui", action="store_true",
                        help="Launch TUI dashboard")
    parser.add_argument("--health", action="store_true",
                        help="Run health check and exit")
    parser.add_argument("--version", action="version", version="SEC-GUY v3.1.0")

    args = parser.parse_args()

    if args.health:
        checker = HealthChecker()
        results = checker.check_all()
        stats = checker.get_system_stats()
        print("\n=== Health Check ===")
        for status in results:
            symbol = "✓" if status.healthy else "✗"
            print(f"  {symbol} {status.component}: {status.error or 'OK'}")
        print(f"\nSystem: CPU {stats['cpu_percent']}% | RAM {stats['memory_percent']}%")
        return 0

    if args.tui:
        from src.ui.tui import SecGuyTUI
        tui = SecGuyTUI()
        tui.run()
        return 0

    # Validate wallet file
    if not args.wallet.exists():
        print(f"[ERROR] Wallet file not found: {args.wallet}")
        return 1

    # Legal disclaimer
    disclaimer = LegalDisclaimer()
    if not disclaimer.require_acceptance():
        print("[ERROR] Legal disclaimer not accepted. Exiting.")
        return 1

    # Biometric gate
    gate = BiometricGate()
    if not gate.require_auth("recovery_session"):
        print("[ERROR] Biometric authentication failed. Exiting.")
        return 1

    # Parse partial seed
    partial_seed = []
    if args.seed:
        partial_seed = args.seed.split()

    # Initialize orchestrator
    get_config()
    orchestrator = SecGuyOrchestrator()

    # Detect or use specified vector
    if args.vector == "auto":
        vector = orchestrator.detect_vector(args.wallet, args.hints, partial_seed)
    else:
        vector_map = {
            "password": RecoveryVector.PASSWORD_HINTED if args.hints else RecoveryVector.PASSWORD_ZERO_HINT,
            "seed": RecoveryVector.SEED_PARTIAL,
            "corruption": RecoveryVector.CORRUPTION,
            "2fa": RecoveryVector.TWOFAA,
        }
        vector = vector_map.get(args.vector, RecoveryVector.UNKNOWN)

    # Submit job
    job = orchestrator.submit_job(args.wallet, args.hints, partial_seed)
    job.vector = vector
    job.confidence = orchestrator.calculate_confidence(job)

    print(f"\n[SEC-GUY] Job {job.job_id} started")
    print(f"[SEC-GUY] Vector: {job.vector.value}")
    print(f"[SEC-GUY] Confidence: {job.confidence:.1f}%")
    print(f"[SEC-GUY] Timeout: {args.timeout} minutes\n")

    # Execute recovery
    result = orchestrator.execute_recovery(job)

    if result.get("success"):
        print("\n[SEC-GUY] ✓ RECOVERY SUCCESSFUL")
        if "password" in result:
            print("[SEC-GUY] Password recovered and stored in vault")
            print(f"[SEC-GUY] Vault entry: {result.get('vault_entry_id', 'N/A')}")
        if "seed_phrase" in result:
            print("[SEC-GUY] Seed phrase recovered and stored in vault")
            print(f"[SEC-GUY] Vault entry: {result.get('vault_entry_id', 'N/A')}")
        print(f"[SEC-GUY] Time: {result.get('time_seconds', 0):.1f}s")
    else:
        print("\n[SEC-GUY] ✗ RECOVERY FAILED")
        print(f"[SEC-GUY] Error: {result.get('error', 'Unknown error')}")
        print("[SEC-GUY] All recovery vectors exhausted.")

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
