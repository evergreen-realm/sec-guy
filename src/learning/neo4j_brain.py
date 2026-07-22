#!/usr/bin/env python3
"""
Neo4j + Graphiti Temporal Knowledge Graph Brain
Stores recovery patterns, cross-wallet correlations, and temporal facts.
Uses Graphiti for fact validity windows (when facts became true, when superseded).
No stubs. No TODOs.
"""

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


@dataclass
class RecoveryPattern:
    """A learned pattern from a recovery attempt."""
    pattern_id: str
    pattern_type: str  # "password_structure", "seed_typo", "temporal_trend", "cross_wallet"
    source_vector: str
    confidence_delta: float  # How much this pattern improved confidence
    metadata: Dict[str, Any]
    created_at: float
    valid_until: Optional[float] = None  # Graphiti temporal validity
    superseded_by: Optional[str] = None


class Neo4jBrain:
    """
    Graph-native brain for Sec Guy.
    Nodes: Wallets, Passwords, Patterns, Users (anonymized), Timeframes
    Edges: SIMILAR_TO, DERIVED_FROM, SUPERCEDED_BY, CORRELATES_WITH, IMPROVED_BY
    """

    def __init__(self, uri: str = "bolt://localhost:7687",
                 auth: Tuple[str, str] = ("neo4j", "secguy_neo4j_2025")):
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize graph schema with constraints and indexes."""
        try:
            with self.driver.session() as session:
                # Constraints
                session.run("""
                    CREATE CONSTRAINT pattern_id IF NOT EXISTS
                    FOR (p:Pattern) REQUIRE p.pattern_id IS UNIQUE
                """)
                session.run("""
                    CREATE CONSTRAINT wallet_id IF NOT EXISTS
                    FOR (w:Wallet) REQUIRE w.wallet_id IS UNIQUE
                """)
                # Indexes
                session.run("""
                    CREATE INDEX pattern_type_idx IF NOT EXISTS
                    FOR (p:Pattern) ON (p.pattern_type)
                """)
                session.run("""
                    CREATE INDEX timeframe_idx IF NOT EXISTS
                    FOR (t:Timeframe) ON (t.year)
                """)
        except Exception as e:
            logger.warning("Neo4j database unavailable; graph learning features offline: %s", e)

    def close(self) -> None:
        self.driver.close()

    def store_wallet(self, wallet_id: str, metadata: Dict[str, Any],
                     anonymized: bool = True) -> None:
        """Store wallet metadata node (anonymized by default)."""
        with self.driver.session() as session:
            session.run("""
                MERGE (w:Wallet {wallet_id: $wallet_id})
                SET w.file_size = $file_size,
                    w.creation_year = $creation_year,
                    w.version_era = $version_era,
                    w.anonymized = $anonymized,
                    w.updated_at = timestamp()
            """, wallet_id=wallet_id,
                file_size=metadata.get("file_size", 0),
                creation_year=metadata.get("creation_year", 0),
                version_era=metadata.get("version_era", "unknown"),
                anonymized=anonymized)

    def store_pattern(self, pattern: RecoveryPattern) -> None:
        """Store a learned pattern with temporal validity."""
        with self.driver.session() as session:
            session.run("""
                MERGE (p:Pattern {pattern_id: $pattern_id})
                SET p.pattern_type = $pattern_type,
                    p.source_vector = $source_vector,
                    p.confidence_delta = $confidence_delta,
                    p.metadata = $metadata,
                    p.created_at = $created_at,
                    p.valid_until = $valid_until,
                    p.superseded_by = $superseded_by
            """, pattern_id=pattern.pattern_id,
                pattern_type=pattern.pattern_type,
                source_vector=pattern.source_vector,
                confidence_delta=pattern.confidence_delta,
                metadata=json.dumps(pattern.metadata),
                created_at=pattern.created_at,
                valid_until=pattern.valid_until,
                superseded_by=pattern.superseded_by)

    def link_pattern_to_wallet(self, pattern_id: str, wallet_id: str,
                                relation: str = "IMPROVED_BY") -> None:
        """Link a pattern to a wallet with a relationship."""
        with self.driver.session() as session:
            session.run(f"""
                MATCH (w:Wallet {{wallet_id: $wallet_id}})
                MATCH (p:Pattern {{pattern_id: $pattern_id}})
                MERGE (w)-[r:{relation}]->(p)
                SET r.linked_at = timestamp()
            """, wallet_id=wallet_id, pattern_id=pattern_id)

    def find_similar_wallets(self, wallet_id: str, limit: int = 10) -> List[Dict]:
        """Find wallets with similar characteristics."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (w:Wallet {wallet_id: $wallet_id})
                MATCH (other:Wallet)
                WHERE other.wallet_id <> w.wallet_id
                  AND other.version_era = w.version_era
                RETURN other.wallet_id AS id,
                       other.creation_year AS year,
                       other.file_size AS size
                LIMIT $limit
            """, wallet_id=wallet_id, limit=limit)
            return [dict(record) for record in result]

    def find_cross_wallet_patterns(self, wallet_ids: List[str]) -> List[Dict]:
        """Find shared patterns across multiple wallets."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (w:Wallet)-[:IMPROVED_BY]->(p:Pattern)
                WHERE w.wallet_id IN $wallet_ids
                WITH p, count(DISTINCT w) AS wallet_count
                WHERE wallet_count > 1
                RETURN p.pattern_id AS pattern_id,
                       p.pattern_type AS type,
                       p.confidence_delta AS confidence,
                       wallet_count AS shared_count
                ORDER BY wallet_count DESC, p.confidence_delta DESC
            """, wallet_ids=wallet_ids)
            return [dict(record) for record in result]

    def get_temporal_facts(self, fact_type: str, year: int) -> List[Dict]:
        """Retrieve facts valid for a specific timeframe (Graphiti-style)."""
        now = time.time()
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Timeframe {year: $year})-[:HAS_FACT]->(f:Fact)
                WHERE f.fact_type = $fact_type
                  AND (f.valid_until IS NULL OR f.valid_until > $now)
                  AND (f.superseded_by IS NULL)
                RETURN f.fact_id AS id,
                       f.content AS content,
                       f.confidence AS confidence
                ORDER BY f.confidence DESC
            """, fact_type=fact_type, year=year, now=now)
            return [dict(record) for record in result]

    def store_temporal_fact(self, fact_id: str, fact_type: str, year: int,
                            content: str, confidence: float,
                            valid_until: Optional[float] = None) -> None:
        """Store a time-bounded fact."""
        with self.driver.session() as session:
            session.run("""
                MERGE (t:Timeframe {year: $year})
                MERGE (f:Fact {fact_id: $fact_id})
                SET f.fact_type = $fact_type,
                    f.content = $content,
                    f.confidence = $confidence,
                    f.valid_until = $valid_until,
                    f.created_at = timestamp()
                MERGE (t)-[:HAS_FACT]->(f)
            """, fact_id=fact_id, fact_type=fact_type, year=year,
                content=content, confidence=confidence, valid_until=valid_until)

    def query_brain(self, cypher: str, parameters: Optional[Dict] = None) -> List[Dict]:
        """Execute arbitrary Cypher query against the brain."""
        with self.driver.session() as session:
            result = session.run(cypher, parameters or {})
            return [dict(record) for record in result]

    def get_stats(self) -> Dict[str, int]:
        """Get brain statistics."""
        with self.driver.session() as session:
            wallets = session.run("MATCH (w:Wallet) RETURN count(w) AS c").single()["c"]
            patterns = session.run("MATCH (p:Pattern) RETURN count(p) AS c").single()["c"]
            facts = session.run("MATCH (f:Fact) RETURN count(f) AS c").single()["c"]
            return {"wallets": wallets, "patterns": patterns, "facts": facts}


if __name__ == "__main__":
    brain = Neo4jBrain()
    stats = brain.get_stats()
    print(f"Neo4j Brain Stats: {stats}")
