"""
Basic import test to verify all modules are loadable.
"""

import importlib
import os
import sys
import pytest

def test_all_modules_import():
    """Import every module in src/ and assert no errors."""
    sys.path.insert(0, os.path.abspath("."))
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py") and not file.startswith("__init__"):
                rel_path = os.path.join(root, file)
                mod_name = rel_path.replace(os.sep, ".").replace(".py", "")
                try:
                    importlib.import_module(mod_name)
                except Exception as e:
                    pytest.fail(f"Failed to import {mod_name}: {e}")
