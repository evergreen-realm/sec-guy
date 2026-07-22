#!/usr/bin/env python3
"""
Cloud AI Client
Free API stacking: Groq, Cerebras, SambaNova, OpenRouter, Google AI Studio.
No stubs. No TODOs.
"""

import time
from typing import Dict, List, Any

import requests


class CloudAIClient:
    """
    Unified client for free cloud AI APIs.
    Implements fallback chain and rate limit tracking.
    """

    ENDPOINTS = {
        "groq": "https://api.groq.com/openai/v1/chat/completions",
        "cerebras": "https://api.cerebras.ai/v1/chat/completions",
        "sambanova": "https://api.sambanova.ai/v1/chat/completions",
        "openrouter": "https://openrouter.ai/api/v1/chat/completions",
        "google": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent",
        "mistral": "https://api.mistral.ai/v1/chat/completions",
        "deepseek": "https://api.deepseek.com/chat/completions",
    }

    MODELS = {
        "groq": "llama-3.3-70b-versatile",
        "cerebras": "llama-3.1-70b",
        "sambanova": "DeepSeek-R1",
        "openrouter": "meta-llama/llama-3.3-70b-instruct",
        "google": "gemini-2.5-flash-preview-05-20",
        "mistral": "mistral-large-latest",
        "deepseek": "deepseek-chat",
    }

    def __init__(self, api_keys: Dict[str, str] = None):
        self.api_keys = api_keys or {}
        self.session = requests.Session()
        self.rate_limits = {k: {"last_call": 0, "calls": 0} for k in self.ENDPOINTS}

    def chat(self, provider: str, messages: List[Dict],
             temperature: float = 0.7, max_tokens: int = 2048) -> Dict[str, Any]:
        """Send chat completion to a specific provider."""
        if provider not in self.ENDPOINTS:
            return {"error": f"Unknown provider: {provider}"}

        api_key = self.api_keys.get(provider)
        if not api_key and provider != "google":
            return {"error": f"No API key for {provider}"}

        url = self.ENDPOINTS[provider]
        model = self.MODELS[provider]

        headers = {"Content-Type": "application/json"}
        if provider == "google":
            url = f"{url}?key={api_key}"
            payload = {
                "contents": [{"role": "user", "parts": [{"text": messages[-1]["content"]}]}],
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
            }
        else:
            headers["Authorization"] = f"Bearer {api_key}"
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

        try:
            resp = self.session.post(url, headers=headers, json=payload, timeout=60)
            self.rate_limits[provider]["last_call"] = time.time()
            self.rate_limits[provider]["calls"] += 1

            if resp.status_code == 200:
                return resp.json()
            return {"error": f"HTTP {resp.status_code}", "detail": resp.text}
        except Exception as e:
            return {"error": str(e)}

    def chat_with_fallback(self, messages: List[Dict],
                           providers: List[str] = None,
                           **kwargs) -> Dict[str, Any]:
        """Try providers in order until one succeeds."""
        providers = providers or ["groq", "cerebras", "sambanova", "openrouter", "google"]
        for provider in providers:
            result = self.chat(provider, messages, **kwargs)
            if "error" not in result:
                return {**result, "provider": provider}
        return {"error": "All providers failed", "attempted": providers}

    def expand_password_hints(self, hints: str, creation_year: int,
                              provider: str = "groq") -> List[str]:
        """Use cloud AI to expand password hints into candidates."""
        prompt = f"""Generate 100 password candidates based on these hints: "{hints}"
Wallet created in {creation_year}.
Consider: pet names, birth years, hobbies, locations, leetspeak, common suffixes.
Output ONE candidate per line, no numbering."""

        messages = [{"role": "user", "content": prompt}]
        result = self.chat(provider, messages, temperature=0.8, max_tokens=4096)

        if "error" in result:
            return []

        # Parse response
        if provider == "google":
            text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        else:
            text = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        candidates = [line.strip() for line in text.split("\n") if line.strip() and not line.strip().startswith("-")]
        return candidates[:200]


if __name__ == "__main__":
    client = CloudAIClient()
    print("Cloud AI Client v3.1")
