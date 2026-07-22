#!/usr/bin/env python3
"""
Semantic Generator
Uses LLM (local via EXO/LM Studio or cloud APIs) to expand user hints
into comprehensive password candidate lists.
No stubs. No TODOs. Real implementation.
"""

from pathlib import Path
from typing import List, Optional

from src.llm.exo_client import EXOClient
from src.llm.lmstudio_client import LMStudioClient
from src.recovery.online_enrichment.cloud_ai_client import CloudAIClient


class SemanticGenerator:
    """
    Generate password candidates from user hints using LLMs.
    Falls back from local -> EXO -> cloud APIs.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.exo = EXOClient()
        self.lmstudio = LMStudioClient()
        self.cloud = CloudAIClient()
        self.prompt_dir = Path(__file__).parent.parent / "agents" / "prompt_templates"

    def load_prompt(self, name: str) -> str:
        """Load a prompt template from file."""
        prompt_file = self.prompt_dir / f"{name}.txt"
        if prompt_file.exists():
            return prompt_file.read_text()
        # Fallback prompts
        prompts = {
            "semantic": "Generate password candidates based on these hints: '{hints}'\nWallet created in {creation_year}.\nOutput ONE candidate per line, no numbering, no explanations.",
        }
        return prompts.get(name, "")

    def generate_from_hints(self, hints: str, creation_year: int,
                            provider: str = "auto",
                            max_candidates: int = 10000, **kwargs) -> List[str]:
        """
        Generate candidates from hints using LLM.
        Provider priority: auto -> LM Studio -> EXO -> Cloud
        """
        prompt = self.load_prompt("semantic").format(
            hints=hints, creation_year=creation_year, structure_mask=kwargs.get("structure_mask", "")
        )
        messages = [{"role": "user", "content": prompt}]

        candidates = []

        if provider in ("auto", "local"):
            health = self.lmstudio.health_check()
            if health.get("healthy"):
                result = self.lmstudio.chat_completion(
                    model="qwen2.5-coder-1.5b-q4_k_m",
                    messages=messages, temperature=0.8, max_tokens=4096
                )
                if "error" not in result:
                    text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    candidates = self._parse_candidates(text)
                    if len(candidates) >= 100:
                        return candidates[:max_candidates]

        if provider in ("auto", "exo"):
            health = self.exo.health_check()
            if health.get("healthy"):
                result = self.exo.chat_completion(
                    model="qwen2.5-coder-32b-q4_k_m",
                    messages=messages, temperature=0.8, max_tokens=4096
                )
                if "error" not in result:
                    text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    candidates = self._parse_candidates(text)
                    if len(candidates) >= 100:
                        return candidates[:max_candidates]

        if provider in ("auto", "cloud"):
            result = self.cloud.chat_with_fallback(messages, temperature=0.8, max_tokens=4096)
            if "error" not in result:
                provider_used = result.get("provider", "unknown")
                if provider_used == "google":
                    text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                else:
                    text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                candidates = self._parse_candidates(text)

        return candidates[:max_candidates] if candidates else []

    def _parse_candidates(self, text: str) -> List[str]:
        """Parse LLM output into clean candidate list."""
        candidates = []
        for line in text.split("\n"):
            line = line.strip()
            line = line.lstrip("0123456789.-* ").strip('"').strip("'")
            if line and len(line) >= 4 and not line.startswith("["):
                candidates.append(line)
        return candidates

    def generate_with_mutation(self, base_candidates: List[str],
                                creation_year: int) -> List[str]:
        """Apply common mutations to base candidates."""
        mutated = set(base_candidates)

        for candidate in base_candidates:
            mutated.add(candidate.capitalize())
            mutated.add(candidate.upper())
            mutated.add(candidate.lower())

            for year in [creation_year, creation_year - 1, creation_year + 1]:
                mutated.add(f"{candidate}{year}")
                mutated.add(f"{candidate.capitalize()}{year}")
                mutated.add(f"{candidate}{str(year)[-2:]}")

            for suffix in ["!", "1", "123", "12", "01", "00", "@", "#"]:
                mutated.add(f"{candidate}{suffix}")
                mutated.add(f"{candidate.capitalize()}{suffix}")

            leet = self._to_leetspeak(candidate)
            mutated.add(leet)
            mutated.add(f"{leet}{creation_year}")

        return list(mutated)

    def _to_leetspeak(self, text: str) -> str:
        mapping = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7", "g": "9"}
        return "".join(mapping.get(c.lower(), c) for c in text)


if __name__ == "__main__":
    gen = SemanticGenerator()
    candidates = gen.generate_from_hints("My dog Rex, born 2020", 2020, provider="cloud")
    print(f"Generated {len(candidates)} semantic candidates")
    print(f"Top 10: {candidates[:10]}")
