#!/usr/bin/env python3
"""
Tokenlist Builder
Constructs semantic tokenlists from hints, CUPP, CeWL, and enrichment data.
No stubs. No TODOs.
"""

import re
from pathlib import Path
from typing import List


class TokenlistBuilder:
    """Build optimized tokenlists for hashcat and btcrecover."""

    def __init__(self, output_dir: Path = Path("/tmp")):
        self.output_dir = output_dir

    def build_from_hints(self, hints: str, creation_year: int,
                         output_path: Path, max_size: int = 100000) -> Path:
        """Build tokenlist from user hints."""
        candidates = set()

        # Parse hints into base words
        base_words = self._extract_base_words(hints)

        # Generate combinations
        for word in base_words:
            candidates.add(word)
            candidates.add(word.lower())
            candidates.add(word.capitalize())
            candidates.add(word.upper())

            # Add year variants
            for year in [creation_year, creation_year - 1, creation_year + 1,
                        str(creation_year)[-2:]]:
                candidates.add(f"{word}{year}")
                candidates.add(f"{word.capitalize()}{year}")
                candidates.add(f"{year}{word}")

            # Add suffixes
            for suffix in ["!", "1", "123", "2020", "@", "#", "$"]:
                candidates.add(f"{word}{suffix}")
                candidates.add(f"{word.capitalize()}{suffix}")

            # Leetspeak
            leet = self._to_leetspeak(word)
            candidates.add(leet)
            candidates.add(f"{leet}{creation_year}")

        # Write to file
        with open(output_path, "w") as f:
            for candidate in sorted(candidates)[:max_size]:
                f.write(candidate + "\n")

        return output_path

    def build_from_cupp(self, cupp_output: Path, output_path: Path) -> Path:
        """Integrate CUPP-generated wordlist."""
        if not cupp_output.exists():
            return output_path

        with open(cupp_output) as src, open(output_path, "a") as dst:
            for line in src:
                dst.write(line)

        return output_path

    def build_from_cewl(self, cewl_output: Path, output_path: Path) -> Path:
        """Integrate CeWL spider output."""
        if not cewl_output.exists():
            return output_path

        with open(cewl_output) as src, open(output_path, "a") as dst:
            for line in src:
                word = line.strip()
                if len(word) >= 4:
                    dst.write(word + "\n")
                    dst.write(word.capitalize() + "\n")

        return output_path

    def build_from_hibp(self, hibp_patterns: List[str], output_path: Path) -> Path:
        """Integrate HIBP breach-derived patterns."""
        with open(output_path, "a") as f:
            for pattern in hibp_patterns:
                f.write(pattern + "\n")
        return output_path

    def _extract_base_words(self, hints: str) -> List[str]:
        """Extract meaningful words from hints."""
        # Remove punctuation, split by spaces
        words = re.findall(r"[A-Za-z0-9]+", hints)
        # Filter out common stop words
        stop_words = {"the", "a", "an", "is", "was", "and", "or", "but", "in", "on", "at"}
        return [w for w in words if w.lower() not in stop_words and len(w) >= 3]

    def _to_leetspeak(self, text: str) -> str:
        """Convert text to leetspeak."""
        mapping = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}
        return "".join(mapping.get(c.lower(), c) for c in text)


if __name__ == "__main__":
    builder = TokenlistBuilder()
    path = builder.build_from_hints("My dog Rex, born 2020", 2020, Path("/tmp/test_tokenlist.txt"))
    print(f"Tokenlist built: {path}")
