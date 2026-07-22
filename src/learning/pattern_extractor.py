#!/usr/bin/env python3
"""
Pattern Extractor
Extracts reusable patterns from successful and failed recovery attempts.
Feeds the Neo4j brain with structured learning data.
No stubs. No TODOs.
"""

import hashlib
import json
import re
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from src.learning.neo4j_brain import Neo4jBrain, RecoveryPattern


@dataclass
class PasswordStructure:
    """Structural pattern extracted from a password."""
    length: int
    has_upper: bool
    has_lower: bool
    has_digit: bool
    has_symbol: bool
    structure_mask: str  # e.g., "ulldds" = upper, lower, lower, digit, digit, symbol
    year_component: Optional[int] = None
    name_component: Optional[str] = None


class PatternExtractor:
    """Extracts patterns from recovery results for brain storage."""

    def __init__(self, brain: Optional[Neo4jBrain] = None):
        self.brain = brain or Neo4jBrain()

    def extract_password_structure(self, password: str) -> PasswordStructure:
        """Analyze password structure without storing the password itself."""
        mask = []
        has_upper = has_lower = has_digit = has_symbol = False
        year_component = None
        name_component = None

        for char in password:
            if char.isupper():
                mask.append("u")
                has_upper = True
            elif char.islower():
                mask.append("l")
                has_lower = True
            elif char.isdigit():
                mask.append("d")
                has_digit = True
            else:
                mask.append("s")
                has_symbol = True

        # Detect year patterns (1900-2030)
        year_match = re.search(r"(19|20)\d{2}", password)
        if year_match:
            year_component = int(year_match.group())

        # Detect common name patterns (simplified)
        common_names = ["rex", "max", "bella", "luna", "charlie", "coco", "rocky"]
        pwd_lower = password.lower()
        for name in common_names:
            if name in pwd_lower:
                name_component = name
                break

        return PasswordStructure(
            length=len(password),
            has_upper=has_upper,
            has_lower=has_lower,
            has_digit=has_digit,
            has_symbol=has_symbol,
            structure_mask="".join(mask),
            year_component=year_component,
            name_component=name_component,
        )

    def store_password_pattern(self, wallet_id: str, password: str,
                               vector: str, confidence_delta: float) -> str:
        """Extract and store password structure pattern (NOT the password)."""
        structure = self.extract_password_structure(password)
        pattern_id = hashlib.sha256(
            f"{wallet_id}:{structure.structure_mask}:{time.time()}".encode()
        ).hexdigest()[:16]

        pattern = RecoveryPattern(
            pattern_id=pattern_id,
            pattern_type="password_structure",
            source_vector=vector,
            confidence_delta=confidence_delta,
            metadata=asdict(structure),
            created_at=time.time(),
        )

        self.brain.store_pattern(pattern)
        self.brain.link_pattern_to_wallet(pattern_id, wallet_id, "IMPROVED_BY")
        return pattern_id

    def extract_seed_pattern(self, seed_phrase: str, missing_positions: List[int],
                             vector: str, confidence_delta: float) -> str:
        """Extract seed recovery pattern."""
        words = seed_phrase.split()
        pattern_id = hashlib.sha256(
            f"seed:{len(words)}:{len(missing_positions)}:{time.time()}".encode()
        ).hexdigest()[:16]

        pattern = RecoveryPattern(
            pattern_id=pattern_id,
            pattern_type="seed_recovery",
            source_vector=vector,
            confidence_delta=confidence_delta,
            metadata={
                "word_count": len(words),
                "missing_count": len(missing_positions),
                "missing_positions": missing_positions,
            },
            created_at=time.time(),
        )

        self.brain.store_pattern(pattern)
        return pattern_id

    def extract_temporal_pattern(self, wallet_id: str, creation_year: int,
                                  successful_password: str, vector: str) -> str:
        """Extract temporal password trend for a specific year."""
        structure = self.extract_password_structure(successful_password)
        pattern_id = hashlib.sha256(
            f"temporal:{creation_year}:{structure.structure_mask}".encode()
        ).hexdigest()[:16]

        # Store as temporal fact in brain
        self.brain.store_temporal_fact(
            fact_id=pattern_id,
            fact_type="password_structure_trend",
            year=creation_year,
            content=json.dumps(asdict(structure)),
            confidence=0.7,
        )

        pattern = RecoveryPattern(
            pattern_id=pattern_id,
            pattern_type="temporal_trend",
            source_vector=vector,
            confidence_delta=5.0,
            metadata={"creation_year": creation_year, "structure": asdict(structure)},
            created_at=time.time(),
        )

        self.brain.store_pattern(pattern)
        self.brain.link_pattern_to_wallet(pattern_id, wallet_id, "IMPROVED_BY")
        return pattern_id

    def extract_cross_wallet_pattern(self, wallet_ids: List[str],
                                     shared_attribute: str,
                                     attribute_type: str) -> str:
        """Extract pattern shared across multiple wallets."""
        pattern_id = hashlib.sha256(
            f"cross:{attribute_type}:{shared_attribute}:{time.time()}".encode()
        ).hexdigest()[:16]

        pattern = RecoveryPattern(
            pattern_id=pattern_id,
            pattern_type="cross_wallet",
            source_vector="cross_wallet_correlator",
            confidence_delta=20.0,
            metadata={
                "wallet_count": len(wallet_ids),
                "attribute_type": attribute_type,
                "shared_attribute": shared_attribute,
            },
            created_at=time.time(),
        )

        self.brain.store_pattern(pattern)
        for wid in wallet_ids:
            self.brain.link_pattern_to_wallet(pattern_id, wid, "CORRELATES_WITH")
        return pattern_id

    def get_patterns_for_wallet(self, wallet_id: str) -> List[Dict]:
        """Retrieve all patterns linked to a wallet."""
        return self.brain.query_brain("""
            MATCH (w:Wallet {wallet_id: $wallet_id})-[:IMPROVED_BY|CORRELATES_WITH]->(p:Pattern)
            RETURN p.pattern_id AS id,
                   p.pattern_type AS type,
                   p.confidence_delta AS confidence,
                   p.created_at AS created
            ORDER BY p.confidence_delta DESC
        """, {"wallet_id": wallet_id})


if __name__ == "__main__":
    extractor = PatternExtractor()
    test_pwd = "Rex2020!"
    struct = extractor.extract_password_structure(test_pwd)
    print(f"Structure of '{test_pwd}': {struct}")
