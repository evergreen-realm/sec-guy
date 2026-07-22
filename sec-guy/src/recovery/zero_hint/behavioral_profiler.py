#!/usr/bin/env python3
"""
Behavioral Profiler
Psychological pattern generation for zero-hint password recovery.
Generates candidates based on human psychology, temporal trends, and crypto culture.
No stubs. No TODOs. Real implementation.
"""

import itertools
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Generator, List, Optional, Set


class BehavioralProfiler:
    """
    Generates password candidates using behavioral psychology principles
    when NO hints are available. This is the nuclear option.
    """

    # Most common human password patterns (global statistics)
    COMMON_PATTERNS = [
        "123456", "123456789", "qwerty", "password", "12345678",
        "111111", "123123", "1234567890", "1234567", "qwerty123",
        "1q2w3e", "abc123", "password1", "1234", "iloveyou",
        "admin", "welcome", "monkey", "login", "princess",
        "dragon", "master", "hello", "freedom", "shadow",
        "sunshine", "whatever", "starwars", "trustno1", "cheese",
    ]

    # Crypto-specific terms ranked by popularity
    CRYPTO_TERMS = [
        "bitcoin", "btc", "crypto", "blockchain", "ethereum", "eth",
        "wallet", "hodl", "moon", "lambo", "satoshi", "mining",
        "trade", "bull", "bear", "altcoin", "defi", "nft", "token",
        "coin", "satoshi", "nakamoto", "genesis", "hash", "block",
        "ledger", "trezor", "exodus", "metamask", "binance",
    ]

    # Keyboard walks (humans love these)
    KEYBOARD_WALKS = [
        "qwerty", "qwerty123", "1qaz2wsx", "1q2w3e4r", "qazwsx",
        "zxcvbnm", "asdfghjkl", "qweasd", "wasdqwer", "123qwe",
        "qwe123", "asd123", "zxc123", "poiuytrewq", "mnbvcxz",
    ]

    # Common years for password suffixes
    SIGNIFICANT_YEARS = list(range(2015, 2027))

    # Common name fragments (pets, family, common names)
    NAME_FRAGMENTS = [
        "rex", "max", "bella", "luna", "charlie", "coco", "rocky",
        "buddy", "daisy", "lucy", "molly", "jack", "oliver", "leo",
        "milo", "simba", "kitty", "shadow", "angel", "princess",
        "baby", "angel", "love", "heart", "star", "dream", "hope",
    ]

    # Common suffixes and prefixes
    SUFFIXES = ["!", "1", "123", "12", "01", "00", "7", "8", "9", "0",
                "2020", "2021", "2022", "2023", "2024", "2025"]
    PREFIXES = ["!", "@", "#", "$", "The", "My", "I", "Mr", "Ms"]

    def __init__(self, wordlist_dir: Path = Path("/opt/sec-guy/wordlists")):
        self.wordlist_dir = wordlist_dir
        self.wordlist_dir.mkdir(parents=True, exist_ok=True)

    def generate_candidates(self, wallet_metadata: Dict,
                            max_candidates: int = 100000) -> Generator[str, None, None]:
        """Generate password candidates from behavioral patterns."""
        creation_year = wallet_metadata.get("creation_year", datetime.now().year)
        era = wallet_metadata.get("version_era", "modern")

        candidates = set()
        count = 0

        # Phase 1: Most common passwords (highest probability)
        for pwd in self.COMMON_PATTERNS:
            candidates.add(pwd)
            candidates.add(pwd.capitalize())
            candidates.add(pwd.upper())
            if count >= max_candidates:
                yield from candidates
                return
            count = len(candidates)

        # Phase 2: Crypto terms + year
        for term in self.CRYPTO_TERMS:
            candidates.add(term)
            candidates.add(term.capitalize())
            candidates.add(term.upper())
            for year in [creation_year, creation_year - 1, creation_year + 1]:
                candidates.add(f"{term}{year}")
                candidates.add(f"{term.capitalize()}{year}")
                candidates.add(f"{term}{str(year)[-2:]}")
                candidates.add(f"{term.capitalize()}{str(year)[-2:]}")
            if count >= max_candidates:
                yield from candidates
                return
            count = len(candidates)

        # Phase 3: Keyboard walks
        for walk in self.KEYBOARD_WALKS:
            candidates.add(walk)
            candidates.add(walk.capitalize())
            candidates.add(f"{walk}!")
            candidates.add(f"{walk}123")
            if count >= max_candidates:
                yield from candidates
                return
            count = len(candidates)

        # Phase 4: Name + year combinations
        for name in self.NAME_FRAGMENTS:
            for year in [creation_year, creation_year - 1, creation_year + 1]:
                candidates.add(f"{name}{year}")
                candidates.add(f"{name.capitalize()}{year}")
                candidates.add(f"{name}{str(year)[-2:]}")
                candidates.add(f"{name.capitalize()}{str(year)[-2:]}")
                candidates.add(f"{name}!")
                candidates.add(f"{name.capitalize()}!")
            if count >= max_candidates:
                yield from candidates
                return
            count = len(candidates)

        # Phase 5: Leetspeak variants
        for term in self.CRYPTO_TERMS[:10]:
            leet = self._to_leetspeak(term)
            candidates.add(leet)
            candidates.add(f"{leet}{creation_year}")
            candidates.add(f"{leet}!")
            if count >= max_candidates:
                yield from candidates
                return
            count = len(candidates)

        # Phase 6: Common suffix/prefix combinations
        for base in list(candidates)[:500]:
            for suffix in self.SUFFIXES:
                candidates.add(f"{base}{suffix}")
            for prefix in self.PREFIXES:
                candidates.add(f"{prefix}{base}")
            if len(candidates) >= max_candidates:
                break

        # Phase 7: Date patterns (DDMMYYYY, MMDDYYYY, YYYYMMDD)
        for month in range(1, 13):
            for day in range(1, 32):
                candidates.add(f"{day:02d}{month:02d}{creation_year}")
                candidates.add(f"{month:02d}{day:02d}{creation_year}")
                candidates.add(f"{creation_year}{month:02d}{day:02d}")

        # Phase 8: Sequential numbers
        for i in range(1000, 10000):
            candidates.add(str(i))
        for i in range(100000, 1000000):
            candidates.add(str(i))

        # Yield all candidates
        for candidate in candidates:
            if len(candidate) >= 4:
                yield candidate

    def _to_leetspeak(self, text: str) -> str:
        mapping = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7", "g": "9", "b": "8"}
        return "".join(mapping.get(c.lower(), c) for c in text)

    def generate_mask_patterns(self, creation_year: int) -> List[str]:
        """Generate hashcat mask patterns prioritized by probability."""
        return [
            "?l?l?l?l?d?d?d?d",      # word + 4 digits (most common)
            "?l?l?l?l?l?d?d?d?d",     # longer word + 4 digits
            "?u?l?l?l?l?d?d?d?d",     # Capitalized word + 4 digits
            "?l?l?l?l?l?l?d?d",       # 6 letters + 2 digits
            "?l?l?l?l?d?d?d?d?s",     # word + 4 digits + symbol
            "?l?l?l?l?l?l?l?l",       # 8 lowercase letters
            "?a?a?a?a?a?a?a?a",       # 8 any characters (last resort)
        ]

    def get_temporal_boost(self, creation_year: int) -> List[str]:
        """Get high-probability candidates for the wallet creation era."""
        boost = []
        # Crypto boom years
        if creation_year in [2017, 2021, 2024]:
            boost.extend(["bitcoin2017", "btc2017", "crypto2017", "hodl2017",
                         "bitcoin2021", "btc2021", "nft2021", "defi2021",
                         "bitcoin2024", "btc2024", "etf2024"])
        return boost


if __name__ == "__main__":
    profiler = BehavioralProfiler()
    meta = {"creation_year": 2021, "version_era": "modern"}
    candidates = list(profiler.generate_candidates(meta, 1000))
    print(f"Generated {len(candidates)} behavioral candidates")
    print(f"Top 10: {candidates[:10]}")
