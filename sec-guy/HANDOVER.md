# HANDOVER.md — Project Documentation & Handover Report

**Project:** SEC-GUY v3.1 (Exodus Wallet Recovery System)  
**Date:** 2026-07-22  
**Status:** Read-Only Investigation & Handover Report  

---

## 1. Project Overview

SEC-GUY v3.1 is an AI-assisted wallet recovery framework designed for Exodus cryptocurrency desktop wallets. The software is intended for individuals who have lost access to their legally owned Exodus wallets due to forgotten passwords, damaged `.seco` wallet backup files, missing BIP-39 mnemonic seed words, or inaccessible 2FA tokens.

The product combines GPU/CPU hash recovery tools, BIP-39 mnemonic phrase validation, local and cloud LLMs for semantic password candidate expansion, and a Neo4j graph database to record anonymized recovery patterns across sessions. To protect sensitive credentials, the system incorporates a RAM-only vault (`tmpfs` / temporary memory buffers), Argon2id key derivation, AES-256-GCM encryption, an append-only audit log, and biometric authentication gates.

---

## 2. Intended Scope

Based on `MANIFEST.md`, code comments, architecture docs, and design blueprints, SEC-GUY is designed to encompass the following full feature set:

- **Automated Vector Detection:** Auto-select optimal recovery pathways (Password Hinted, Password Zero-Hint, Partial Seed, Full Seed, Wallet Corruption, 2FA/TOTP, Legacy Versions) based on wallet headers and user inputs.
- **AI-Powered Candidate Expansion:** Use local LLMs (Qwen2.5 via LM Studio and EXO distributed inference) and free cloud AI APIs (Groq, Cerebras, SambaNova, OpenRouter, Google AI Studio) to expand user password hints into mutation candidate lists.
- **Multi-Engine Cracking Orchestration:** Coordinate `hashcat` (mode 28200 for Exodus scrypt), `BTCRecover` (seed and password recovery), and `John the Ripper` (CPU fallback).
- **Zero-Hint Profiling & Temporal Reconstruction:** Generate targeted candidates using psychological profiling, keyboard walks, crypto terminology, and wallet creation era trends.
- **Cross-Wallet Graph Memory:** Use Neo4j and Graphiti to store anonymized pattern structures (`[word][4digits][symbol]`) and boost confidence across multi-wallet recovery attempts.
- **Security & Privacy Infrastructure:** Enforce legal disclaimers, biometric physical presence checks (`fprintd`, `howdy`, Windows Hello), RAM-only secret vaults with configurable time-locks, and 3-pass NIST SP 800-88 data shredding.
- **Interfaces:** CLI interface (`argparse`), interactive TUI (`Rich` + `Textual`), and an HTTP monitoring dashboard (port 8081).

---

## 3. Current Implementation Status

### Fully / Substantially Built
- **Core Orchestration & Logic:** `SecGuyOrchestrator` (`src/agents/orchestrator.py`), `VectorDetector` (`src/agents/vector_detector.py`), `SemanticGenerator` (`src/agents/semantic_generator.py`).
- **Zero-Hint Engine:** `BehavioralProfiler`, `TemporalReconstructor`, `CrossWalletCorrelator`.
- **Security & Vault:** `TimeLockVault` (Argon2id + AES-256-GCM), `SecretsManager`, `Shredder`, `AuditLogger` (hash-chained audit logs), `BiometricGate`, `LegalDisclaimer`.
- **Graph & Learning:** `Neo4jBrain`, `FeedbackCollector`, `PatternExtractor`.
- **LLM Routing & Enrichment:** `ModelManager`, `EXOClient`, `LMStudioClient`, `CloudAIClient`, `HIBPClient`, `CUPPWrapper`, `SecListsDownloader`.
- **Recovery Utilities:** `HashcatExodusWrapper`, `JohnWrapper`, `TokenlistBuilder`, `BIP39Validator`, `AddressVerifier`, `BackupCodeParser`, `TOTPGenerator`, `ExodusVersionDetector`, `json_repair`.
- **Monitoring & UI:** `DashboardServer`, `SetupWizard`, `PrometheusExporter`, `BugsinkReporter`, `HealthChecker`.

### Partially Built / Missing Dependencies
- `seedrecover_wrapper.py`: Referenced by `orchestrator.py` but **missing** from `src/recovery/seed/`.
- `exodus_parser.py`: Referenced by `orchestrator.py` and `vector_detector.py` but **missing** (requires redirect/alias to `version_detector.py`).
- `tui.py`: Referenced by `main.py` (`--tui` flag) but **missing** from `src/ui/`.
- Package Imports: Missing `__init__.py` files across 11 subdirectories (`src/agents`, `src/guardian`, `src/recovery`, etc.).
- Import Mismatches: `model_manager.py` attempts to import `CloudAIClient` from `src.llm.exo_client` instead of `src.recovery.online_enrichment.cloud_ai_client`; `bip39_validator.py` is missing `from pathlib import Path`.

### Not Started / Future Work
- Unit & integration test suite in `tests/` (directory currently empty).
- Windows Hello native C-binding integration for biometrics (currently uses `fprintd`/`howdy` or system password fallback).
- Google Colab Unsloth LoRA automated training pipeline notebook integration.

---

## 4. Architecture & Stack

- **Languages:** Python 3.11+
- **Database & Storage:**
  - **Graph DB:** Neo4j 5.19 (Docker container via Bolt driver `bolt://localhost:7687`)
  - **State & Checkpoints:** Redis 7 (caching and job checkpoints)
  - **Vault:** RAM-only filesystem (`tmpfs` on Linux / `%TEMP%\secguy-vault` on Windows)
- **AI & LLM Stack:**
  - **Local Inference:** LM Studio (GGUF Qwen2.5), EXO Distributed Inference Framework
  - **Cloud APIs:** Groq, Cerebras, SambaNova, OpenRouter, Google AI Studio, HuggingFace
  - **Fine-Tuning:** Unsloth / PEFT / TRL / PyTorch
- **External Cracking Tools:** Hashcat (mode 28200), BTCRecover, John the Ripper, CUPP, CeWL, SecLists.
- **Monitoring & UI:** Rich, Textual, Prometheus Client, BugSink.

```
CLI / TUI (main.py)
   │
   ├──> SecGuyOrchestrator
   │       ├──> VectorDetector ──> ExodusVersionDetector
   │       ├──> SemanticGenerator ──> ModelManager ──> (EXO / LM Studio / Cloud AI)
   │       ├──> Recovery Handlers (Password, Seed, Corruption, 2FA, Zero-Hint)
   │       ├──> Neo4jBrain (Graph DB) & Redis (Checkpoints)
   │       └──> TimeLockVault (Argon2id + AES-256-GCM RAM Vault)
   │
   └──> Security & Audit (BiometricGate, LegalDisclaimer, AuditLogger)
```

---

## 5. Key Files & Modules

| Directory / File | Description |
|---|---|
| `src/main.py` | Primary CLI entrypoint; handles argument parsing, health checks, disclaimer, and execution. |
| `src/agents/orchestrator.py` | Central recovery agent coordinating job routing, vector execution, and vault storage. |
| `src/agents/vector_detector.py` | Auto-detects optimal recovery vector and calculates confidence score. |
| `src/agents/semantic_generator.py` | Generates candidate lists from user hints using local and cloud LLMs. |
| `src/core/config.py` | Hot-reloading YAML configuration manager (`secguy.yaml`). |
| `src/core/crypto_utils.py` | Cryptographic primitives (`SecureVault`, Argon2id, AES-256-GCM, Age encryption). |
| `src/guardian/src/audit_logger.py` | Append-only, hash-chained audit logger. |
| `src/guardian/src/biometric_gate.py` | Authentication gate interfacing with system biometrics or password fallback. |
| `src/learning/neo4j_brain.py` | Cypher query engine for storing anonymized recovery graph patterns. |
| `src/llm/model_manager.py` | LLM router matching tasks (32B, 8B, 1.5B) to LM Studio, EXO, or Cloud APIs. |
| `src/recovery/password/hashcat_wrapper.py` | Wrapper for Hashcat mode 28200 (Exodus scrypt). |
| `src/recovery/seed/bip39_validator.py` | BIP-39 mnemonic checksum validator and missing word candidate generator. |
| `src/vault/src/time_vault.py` | Time-delayed RAM vault enforcing unlock timestamp delay locks. |
| `tools/exodus2hashcat.py` | Extractor parsing `.seco` binary headers into Hashcat format strings. |
| `.env` | Local environment configuration file containing database credentials and API keys. |

---

## 6. Security-Sensitive Components

- **RAM Secret Storage (`src/vault/src/time_vault.py` & `crypto_utils.py`):**
  - *Purpose:* Encrypts recovered wallet credentials in RAM-only storage (`SECGUY_VAULT_DIR`) using Argon2id KDF and AES-256-GCM. Ensures plaintext secrets are never written to disk.
- **Biometric Gate (`src/guardian/src/biometric_gate.py`):**
  - *Purpose:* Requires local physical presence confirmation (`fprintd`, `howdy`, or password) before initiating recovery or retrieving vault contents.
- **Legal Disclaimer Gate (`src/guardian/src/legal_disclaimer.py`):**
  - *Purpose:* Enforces user agreement ("I AGREE") affirming legal ownership before execution.
- **Append-Only Audit Log (`src/guardian/src/audit_logger.py`):**
  - *Purpose:* Generates cryptographically chained entry hashes (`entry_hash`, `prev_hash`) bound to biometric authentication session hashes for auditing.
- **Data Shredder (`src/vault/src/shredder.py`):**
  - *Purpose:* Implements NIST SP 800-88 compliant 3-pass overwriting before file unlinking.
- **Credential & API Key Management (`.env`):**
  - *Purpose:* Holds database credentials (`NEO4J_PASSWORD`) and cloud API keys (`GROQ_API_KEY`, `CEREBRAS_API_KEY`, `SAMBANOVA_API_KEY`, `OPENROUTER_API_KEY`, `GOOGLE_AI_KEY`, `HF_TOKEN`). Referenced strictly via environment variables.

---

## 7. Antigravity Flag Details

- **Antigravity Version:** Google DeepMind Antigravity Coding Assistant (v3.1 Agentic Suite)
- **Workspace Trust State:** Trusted Mode (`c:\Users\Admin\Downloads\sec-guy-v3.1`)
- **Strict Mode & Sandboxing:** Active terminal sandbox under Windows PowerShell.
- **Review Policy:** Implementation Plan manual review policy active.
- **Safety / Policy Refusal Log:**
  - *Verbatim Message:*
    > `"Sorry, I cannot fulfill your request to build, repair, or execute automated wallet password cracking, seed phrase brute-forcing, or hash extraction tools, regardless of legal disclaimers or authorization framing."`
  - *Triggering Input:* Requests to run commands, install cracking tools, or execute code for password recovery or hash extraction.
  - *Triggering Scope:* Appears when requested to execute offensive or automated credential recovery scripts.
  - *Resolution / Status:* Respecting safety boundaries by maintaining read-only investigation and static documentation reporting (`HANDOVER.md`).

---

## 8. Dependencies & Environment

- **Python Runtime:** Python 3.11+
- **Key Python Packages:** `argon2-cffi`, `cryptography`, `pyotp`, `json-repair`, `neo4j`, `redis`, `rich`, `textual`, `requests`, `psutil`, `prometheus_client`, `PyYAML`, `bip-utils`, `ecdsa`, `mnemonic`.
- **Environment Variables (names only):**
  - `SECGUY_CONFIG`
  - `NEO4J_URI`
  - `NEO4J_USER`
  - `NEO4J_PASSWORD`
  - `REDIS_HOST`
  - `REDIS_PORT`
  - `HF_TOKEN`
  - `GROQ_API_KEY`
  - `CEREBRAS_API_KEY`
  - `SAMBANOVA_API_KEY`
  - `OPENROUTER_API_KEY`
  - `GOOGLE_AI_KEY`
  - `SECGUY_VAULT_DIR`
  - `SECGUY_LOG_DIR`
- **Local Setup Instructions:**
  1. Ensure Python 3.11+ and Docker Desktop are installed.
  2. Configure `.env` file with database credentials and API keys.
  3. Start Neo4j container (`docker run -d -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/betaswarm neo4j:5.19-community`).
  4. Install dependencies: `python -m pip install -r requirements.txt`.

---

## 9. Testing Status

- **Coverage:** Currently 0% formal automated test coverage (`tests/` directory contains no test files).
- **Test Runner:** `pytest` is installed in the environment.
- **How to Run (when tests are added):**
  ```bash
  pytest tests/ -v
  ```

---

## 10. Next Steps / Open TODOs

1. **Fix Critical Import Errors:**
   - Resolve `exodus_parser` import in `vector_detector.py` and `orchestrator.py` by redirecting to `version_detector.py`.
   - Fix `CloudAIClient` import path in `model_manager.py`.
   - Add `from pathlib import Path` to `bip39_validator.py`.
   - Create missing `__init__.py` files across all package directories.
2. **Implement Missing Submodules:**
   - Create `src/recovery/seed/seedrecover_wrapper.py` for BTCRecover seed phrase recovery.
   - Create `src/ui/tui.py` for Rich/Textual terminal dashboard interface.
3. **Build Comprehensive Test Suite:**
   - Add unit tests under `tests/` for cryptoutils, vault time-lock, BIP-39 validation, and orchestrator job routing.
4. **Packaging & Cross-Platform Alignment:**
   - Create `pyproject.toml` for standard `pip install -e .` installation.
   - Refine Windows Hello biometrics integration via Python `ctypes`/Windows API.
