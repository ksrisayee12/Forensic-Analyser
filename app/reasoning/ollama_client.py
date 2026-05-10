"""
AIVENTRA — Async Ollama HTTP Client (Phase 13)
Direct httpx-based client for Ollama REST API. No LangChain.
"""
from __future__ import annotations

import json
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.core.exceptions import OllamaConnectionError, ReasoningError


class OllamaClient:
    """
    Async HTTP client for the Ollama local LLM API.
    Supports streaming and non-streaming completions.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.OLLAMA_TIMEOUT

    # ------------------------------------------------------------------
    # Health / model listing
    # ------------------------------------------------------------------

    async def is_available(self) -> bool:
        """Check if Ollama server is running."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        """Return list of locally available Ollama model names."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            raise OllamaConnectionError(f"Failed to list Ollama models: {e}")

    # ------------------------------------------------------------------
    # Completions
    # ------------------------------------------------------------------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> str:
        """
        Non-streaming text generation via Ollama /api/generate.

        Returns:
            Generated text string.
        """
        model = model or settings.OLLAMA_DEFAULT_MODEL
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": 300,          # Keep model loaded for 5 min between requests
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": 4096,         # Cap context window; prevents slow unbounded alloc
            },
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "")
        except httpx.ConnectError as e:
            raise OllamaConnectionError(
                f"Ollama server at {self.base_url} is not reachable. "
                "Ensure Ollama is running: `ollama serve`"
            ) from e
        except Exception as e:
            raise ReasoningError(f"Ollama generation failed: {e}") from e

    async def generate_stream(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        temperature: float = 0.1,
    ) -> AsyncGenerator[str, None]:
        """
        Streaming text generation via Ollama /api/generate.

        Yields:
            Text chunks as they are generated.
        """
        model = model or settings.OLLAMA_DEFAULT_MODEL
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=payload,
            ) as resp:
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("response", "")
                        if token:
                            yield token
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> str:
        """
        Chat completion via Ollama /api/chat.

        Args:
            messages: List of {role, content} dicts.

        Returns:
            Assistant reply string.
        """
        model = model or settings.OLLAMA_DEFAULT_MODEL
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "keep_alive": 300,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": 4096,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content", "")
        except httpx.ConnectError as e:
            raise OllamaConnectionError(
                f"Ollama server unreachable at {self.base_url}."
            ) from e
        except Exception as e:
            raise ReasoningError(f"Ollama chat failed: {e}") from e


# Module-level singleton
ollama = OllamaClient()
