"""
CropNet AI — Local Ollama Runtime Adapter.

Provides a modular, secure interface to local Ollama running Qwen3:8B.
Strictly local: never exposes Ollama externally; only internal backend
services may communicate with this client.
"""
import logging
import time
from typing import Dict, Any, List, Optional
import httpx

from cropnet.services.api.app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Adapter for communicating with the local Ollama daemon.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout_seconds: Optional[int] = None
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.default_model = default_model or settings.OLLAMA_MODEL
        self.timeout_seconds = timeout_seconds or settings.OLLAMA_TIMEOUT_SECONDS

    def is_available(self) -> bool:
        """
        Check if the local Ollama server is responsive.
        """
        if not settings.OLLAMA_ENABLED:
            return False
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama server not reachable at {self.base_url}: {e}")
            return False

    def is_model_available(self, model_name: Optional[str] = None) -> bool:
        """
        Verify that the requested model is downloaded and loaded in Ollama.
        """
        target = model_name or self.default_model
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    # Direct match or prefix match (e.g. qwen3:8b in qwen3:8b)
                    return any(target in m or m.startswith(target) for m in models)
                return False
        except Exception as e:
            logger.debug(f"Error checking model {target} in Ollama: {e}")
            return False

    async def a_is_available(self) -> bool:
        """Async check for Ollama daemon availability."""
        if not settings.OLLAMA_ENABLED:
            return False
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def a_is_model_available(self, model_name: Optional[str] = None) -> bool:
        """Async check for target model availability in Ollama."""
        target = model_name or self.default_model
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    return any(target in m or m.startswith(target) for m in models)
                return False
        except Exception:
            return False

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Synchronous chat completion with local Ollama.
        """
        target_model = model or self.default_model
        target_temp = temperature if temperature is not None else settings.OLLAMA_TEMPERATURE
        target_max_tokens = max_tokens or settings.OLLAMA_MAX_TOKENS
        req_timeout = timeout or self.timeout_seconds

        payload = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": target_temp,
                "num_predict": target_max_tokens
            }
        }

        start_t = time.time()
        timeout_config = httpx.Timeout(
            timeout=float(req_timeout),
            connect=3.0,
            read=float(req_timeout),
            write=10.0,
            pool=5.0
        )
        try:
            with httpx.Client(timeout=timeout_config) as client:
                resp = client.post(f"{self.base_url}/api/chat", json=payload)
                elapsed = time.time() - start_t

                if resp.status_code != 200:
                    logger.error(f"Ollama chat error HTTP {resp.status_code}: {resp.text}")
                    return {
                        "success": False,
                        "error": f"HTTP {resp.status_code}: {resp.text}",
                        "content": None,
                        "latency_seconds": elapsed
                    }

                data = resp.json()
                msg = data.get("message", {})
                content = msg.get("content", "").strip()

                # Clean thinking tags if present
                if "<think>" in content and "</think>" in content:
                    parts = content.split("</think>", 1)
                    content = parts[1].strip()

                return {
                    "success": True,
                    "content": content,
                    "model": data.get("model", target_model),
                    "total_duration": data.get("total_duration"),
                    "eval_count": data.get("eval_count"),
                    "latency_seconds": elapsed
                }
        except httpx.TimeoutException:
            elapsed = time.time() - start_t
            logger.warning(f"Ollama inference timed out after {elapsed:.2f}s (limit: {req_timeout}s)")
            return {
                "success": False,
                "error": f"Inference timed out after {req_timeout}s",
                "content": None,
                "latency_seconds": elapsed
            }
        except httpx.ConnectError as e:
            elapsed = time.time() - start_t
            logger.warning(f"Could not connect to Ollama at {self.base_url}: {e}")
            return {
                "success": False,
                "error": f"Connection refused at {self.base_url}",
                "content": None,
                "latency_seconds": elapsed
            }
        except Exception as e:
            elapsed = time.time() - start_t
            logger.error(f"Unexpected error during Ollama invocation: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": None,
                "latency_seconds": elapsed
            }

    async def a_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Asynchronous chat completion with local Ollama.
        """
        target_model = model or self.default_model
        target_temp = temperature if temperature is not None else settings.OLLAMA_TEMPERATURE
        target_max_tokens = max_tokens or settings.OLLAMA_MAX_TOKENS
        req_timeout = timeout or self.timeout_seconds

        payload = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": target_temp,
                "num_predict": target_max_tokens
            }
        }

        start_t = time.time()
        timeout_config = httpx.Timeout(
            timeout=float(req_timeout),
            connect=3.0,
            read=float(req_timeout),
            write=10.0,
            pool=5.0
        )
        try:
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                elapsed = time.time() - start_t

                if resp.status_code != 200:
                    logger.error(f"Ollama async chat error HTTP {resp.status_code}: {resp.text}")
                    return {
                        "success": False,
                        "error": f"HTTP {resp.status_code}: {resp.text}",
                        "content": None,
                        "latency_seconds": elapsed
                    }

                data = resp.json()
                msg = data.get("message", {})
                content = msg.get("content", "").strip()

                if "<think>" in content and "</think>" in content:
                    parts = content.split("</think>", 1)
                    content = parts[1].strip()

                return {
                    "success": True,
                    "content": content,
                    "model": data.get("model", target_model),
                    "total_duration": data.get("total_duration"),
                    "eval_count": data.get("eval_count"),
                    "latency_seconds": elapsed
                }
        except httpx.TimeoutException:
            elapsed = time.time() - start_t
            logger.warning(f"Ollama async inference timed out after {elapsed:.2f}s")
            return {
                "success": False,
                "error": f"Inference timed out after {req_timeout}s",
                "content": None,
                "latency_seconds": elapsed
            }
        except httpx.ConnectError as e:
            elapsed = time.time() - start_t
            return {
                "success": False,
                "error": f"Connection refused at {self.base_url}",
                "content": None,
                "latency_seconds": elapsed
            }
        except Exception as e:
            elapsed = time.time() - start_t
            return {
                "success": False,
                "error": str(e),
                "content": None,
                "latency_seconds": elapsed
            }
