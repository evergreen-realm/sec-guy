import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.agents.orchestrator import SecGuyOrchestrator, RecoveryVector

class TestOrchestrator(unittest.TestCase):
    @patch("src.learning.neo4j_brain.GraphDatabase")
    def test_submit_job_and_vector_detection(self, mock_graph):
        orch = SecGuyOrchestrator()
        job = orch.submit_job(Path("non_existent_wallet.seco"), hints="mysecret123")
        self.assertIsNotNone(job.job_id)
        self.assertEqual(job.vector, RecoveryVector.PASSWORD_HINTED)
        self.assertIn(job.job_id, orch.jobs)

    @patch("src.learning.neo4j_brain.GraphDatabase")
    def test_partial_seed_vector(self, mock_graph):
        orch = SecGuyOrchestrator()
        job = orch.submit_job(Path("test.seco"), partial_seed=["apple", "banana", "cherry", "date", "elderberry", "fig", "grape", "honeydew", "?", "?", "?", "?"])
        self.assertEqual(job.vector, RecoveryVector.SEED_PARTIAL)

if __name__ == "__main__":
    unittest.main()
