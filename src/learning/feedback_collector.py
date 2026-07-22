#!/usr/bin/env python3
"""
Feedback Collector
Collects results from recovery attempts and feeds them back into the brain.
Implements the learning feedback loop.
No stubs. No TODOs.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.learning.neo4j_brain import Neo4jBrain
from src.learning.pattern_extractor import PatternExtractor


class FeedbackCollector:
    """
    Closes the learning loop:
    Recovery result -> Pattern extraction -> Brain storage -> Strategy adjustment
    """

    def __init__(self, brain: Optional[Neo4jBrain] = None,
                 extractor: Optional[PatternExtractor] = None):
        self.brain = brain or Neo4jBrain()
        self.extractor = extractor or PatternExtractor(self.brain)
        self.feedback_log: List[Dict] = []

    def record_success(self, job_id: str, wallet_id: str, vector: str,
                       result: Dict[str, Any], initial_confidence: float) -> Dict:
        """Record a successful recovery and extract patterns."""
        final_confidence = 100.0
        confidence_delta = final_confidence - initial_confidence

        feedback = {
            "job_id": job_id,
            "wallet_id": wallet_id,
            "vector": vector,
            "success": True,
            "initial_confidence": initial_confidence,
            "final_confidence": final_confidence,
            "confidence_delta": confidence_delta,
            "time_seconds": result.get("time_seconds", 0),
            "timestamp": time.time(),
        }

        # Extract patterns based on vector
        if vector == "password_hinted" or vector == "password_zero_hint":
            password = result.get("password", "")
            if password:
                pattern_id = self.extractor.store_password_pattern(
                    wallet_id, password, vector, confidence_delta
                )
                feedback["pattern_id"] = pattern_id

        elif vector == "seed_partial":
            seed = result.get("seed_phrase", "")
            missing = result.get("missing_words", [])
            if seed:
                pattern_id = self.extractor.extract_seed_pattern(
                    seed, list(range(len(missing))), vector, confidence_delta
                )
                feedback["pattern_id"] = pattern_id

        self.feedback_log.append(feedback)
        return feedback

    def record_failure(self, job_id: str, wallet_id: str, vector: str,
                       initial_confidence: float, error: str) -> Dict:
        """Record a failed recovery for negative learning."""
        feedback = {
            "job_id": job_id,
            "wallet_id": wallet_id,
            "vector": vector,
            "success": False,
            "initial_confidence": initial_confidence,
            "final_confidence": 0.0,
            "confidence_delta": -initial_confidence,
            "error": error,
            "timestamp": time.time(),
        }
        self.feedback_log.append(feedback)
        return feedback

    def get_strategy_adjustments(self, vector: str, wallet_metadata: Dict) -> List[Dict]:
        """Get strategy adjustments based on learned patterns."""
        adjustments = []

        # Check temporal patterns
        creation_year = wallet_metadata.get("creation_year", 0)
        if creation_year > 0:
            temporal_facts = self.brain.get_temporal_facts(
                "password_structure_trend", creation_year
            )
            if temporal_facts:
                adjustments.append({
                    "type": "temporal_prioritization",
                    "priority": "high",
                    "reason": f"Found {len(temporal_facts)} temporal patterns for {creation_year}",
                    "facts": temporal_facts[:3],
                })

        # Check cross-wallet patterns
        similar = self.brain.find_similar_wallets(wallet_metadata.get("wallet_id", ""))
        if similar:
            wallet_ids = [w["id"] for w in similar]
            cross_patterns = self.brain.find_cross_wallet_patterns(wallet_ids)
            if cross_patterns:
                adjustments.append({
                    "type": "cross_wallet_boost",
                    "priority": "medium",
                    "reason": f"Found {len(cross_patterns)} shared patterns",
                    "patterns": cross_patterns[:3],
                })

        return adjustments

    def export_feedback_log(self, path: Path) -> None:
        """Export feedback log to JSON for analysis."""
        with open(path, "w") as f:
            json.dump(self.feedback_log, f, indent=2)

    def get_learning_stats(self) -> Dict:
        """Get statistics on learning progress."""
        total = len(self.feedback_log)
        successes = sum(1 for f in self.feedback_log if f["success"])
        failures = total - successes
        avg_delta = sum(f["confidence_delta"] for f in self.feedback_log) / total if total > 0 else 0

        return {
            "total_attempts": total,
            "successes": successes,
            "failures": failures,
            "success_rate": successes / total if total > 0 else 0,
            "avg_confidence_delta": avg_delta,
            "brain_stats": self.brain.get_stats(),
        }


if __name__ == "__main__":
    collector = FeedbackCollector()
    stats = collector.get_learning_stats()
    print(f"Learning Stats: {stats}")
