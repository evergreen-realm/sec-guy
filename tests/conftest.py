
import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def temp_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_wallet_file(temp_project):
    wallet_path = temp_project / "wallet.seco"
    wallet_path.write_bytes(b"SECO" + b"\x00" * 20)
    return wallet_path

@pytest.fixture
def sample_seed_phrase():
    return ["abandon","ability","able","about","above","absent","absorb","abstract","absurd","abuse","access","accident"]
