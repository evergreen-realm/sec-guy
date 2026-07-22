#!/usr/bin/env python3
"""
LM Studio API Client
Connects to LM Studio running locally for fast model switching.
No stubs. No TODOs.
"""

import json
import time
from typing import Dict, List, Optional, Any

import requests


class LMStudioClient:
    """
    Client for LM Studio local inference server.
    Used for quick semantic generation on T490 with small models.
    """

    def __init__(self, base_url: str = "http://localhost:1234/v1"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def health_check(self) -> Dict[str, Any]:
        """Check if LM Studio server is running."""
        try:
            resp = self.session.get(f"{self.base_url}/models", timeout=5)
            if resp.status_code == 200:
                models = resp.json().get("data", [])
                return {"healthy": True, "loaded_models": len(models), "models": models}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
        return {"healthy": False, "error": "No response"}

    def load_model(self, model_path: str) -> Dict[str, Any]:
        """Request LM Studio to load a specific model."""
        payload = {"model": model_path}
        try:
            resp = self.session.post(
                f"{self.base_url}/models/load",
                json=payload,
                timeout=60
            )
            return {"success": resp.status_code == 200, "detail": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def chat_completion(self, model: str, messages: List[Dict],
                        temperature: float = 0.7, max_tokens: int = 2048) -> Dict[str, Any]:
        """Send chat completion to LM Studio."""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        try:
            resp = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=120
            )
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"HTTP {resp.status_code}", "detail": resp.text}
        except Exception as e:
            return {"error": str(e)}

    def unload_model(self, model: str) -> Dict[str, Any]:
        """Unload a model to free RAM."""
        try:
            resp = self.session.post(
                f"{self.base_url}/models/unload",
                json={"model": model},
                timeout=30
            )
            return {"success": resp.status_code == 200}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_loaded_models(self) -> List[Dict]:
        """Get list of currently loaded models."""
        try:
            resp = self.session.get(f"{self.base_url}/models", timeout=5)
            if resp.status_code == 200:
                return resp.json().get("data", [])
        except Exception:
            pass
        return []


if __name__ == "__main__":
    client = LMStudioClient()
    health = client.health_check()
    print(f"LM Studio Health: {health}")
