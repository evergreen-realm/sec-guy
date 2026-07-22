#!/usr/bin/env python3
"""
Sec Guy Constants
Version maps, magic bytes, BIP39 wordlist, hashcat modes.
No stubs. No TODOs.
"""

from pathlib import Path

VERSION = "3.1.0"
BUILD_DATE = "2026-05-25"

# Exodus secure-container magic bytes
EXODUS_SECO_MAGIC = b"SECO"
EXODUS_SECO_MAGIC_ALT = b"\x00seco"
EXODUS_HEADER_SIZE = 224
EXODUS_METADATA_SIZE = 256

# Hashcat
HASHCAT_MODE_EXODUS = 28200
HASHCAT_JOHN_FALLBACK_FORMAT = "exodus"

# scrypt parameters by Exodus era
SCRYPT_PARAMS = {
    "legacy": {"n": 16384, "r": 8, "p": 1, "era": "v1.x-v18.x"},
    "modern": {"n": 16384, "r": 8, "p": 1, "era": "v19.x-v22.x"},
    "current": {"n": 32768, "r": 8, "p": 1, "era": "v23.x-v25.x+"},
}

# BIP39
BIP39_WORD_COUNT = 12
BIP39_ENTROPY_BITS = 128
BIP39_CHECKSUM_BITS = 4
BIP39_WORDLIST_URL = "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt"

# Vault
VAULT_MOUNT = "/dev/shm/secguy-vault"
VAULT_MAX_SIZE_MB = 100
VAULT_TTL_SECONDS = 300
VAULT_CIPHER = "age"
VAULT_TIME_LOCK = "argon2id"

# Recovery confidence targets
CONFIDENCE_TARGETS = {
    "password_hinted": 35.0,
    "password_zero_hint": 15.0,
    "seed_partial": 90.0,
    "seed_full": 99.0,
    "corruption": 70.0,
    "twofa": 55.0,
    "legacy": 60.0,
}

# Free API endpoints
FREE_APIS = {
    "google": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent",
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "cerebras": "https://api.cerebras.ai/v1/chat/completions",
    "sambanova": "https://api.sambanova.ai/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "mistral": "https://api.mistral.ai/v1/chat/completions",
    "cloudflare": "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/meta/llama-3.1-8b-instruct",
    "huggingface": "https://api-inference.huggingface.co/models/",
    "github_models": "https://models.inference.ai.azure.com/chat/completions",
    "deepseek": "https://api.deepseek.com/chat/completions",
}

# File paths
PROJECT_ROOT = Path("/opt/sec-guy")
CONFIG_PATH = PROJECT_ROOT / "config" / "secguy.yaml"
MODELS_DIR = PROJECT_ROOT / "models"
TOOLS_DIR = PROJECT_ROOT / "tools"
WORDLISTS_DIR = PROJECT_ROOT / "wordlists"
ENRICHMENT_DIR = PROJECT_ROOT / "enrichment_data"
TESTS_DIR = PROJECT_ROOT / "tests"
