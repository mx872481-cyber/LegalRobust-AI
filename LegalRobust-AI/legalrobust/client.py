
"""Minimal OpenAI-compatible Chat Completions client using the Python stdlib."""
from __future__ import annotations
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any


class ModelClientError(RuntimeError):
    pass


class ChatClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None,
                 model: str | None = None, timeout: int | None = None,
                 max_retries: int | None = None):
        self.base_url = (base_url or os.getenv("LEGALROBUST_BASE_URL", "")).rstrip("/")
        self.api_key = api_key if api_key is not None else os.getenv("LEGALROBUST_API_KEY", "")
        self.model = model or os.getenv("LEGALROBUST_MODEL", "")
        self.timeout = timeout or int(os.getenv("LEGALROBUST_TIMEOUT", "90"))
        self.max_retries = max_retries if max_retries is not None else int(os.getenv("LEGALROBUST_MAX_RETRIES", "2"))
        if not self.base_url:
            raise ModelClientError("Missing LEGALROBUST_BASE_URL.")
        if not self.model:
            raise ModelClientError("Missing model ID. Set LEGALROBUST_MODEL or pass model=.")
        if not self.base_url.startswith(("https://", "http://localhost", "http://127.0.0.1")):
            raise ModelClientError("Use HTTPS for remote endpoints. HTTP is allowed only for localhost.")

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.0,
             max_tokens: int = 1200, model: str | None = None) -> str:
        url = self.base_url + "/chat/completions"
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(url, data=data, headers=headers, method="POST")
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    raw = response.read().decode("utf-8")
                obj = json.loads(raw)
                return obj["choices"][0]["message"]["content"] or ""
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")[:1000]
                # Do not retry common permanent client errors.
                if exc.code in (400, 401, 403, 404, 422):
                    raise ModelClientError(f"Provider HTTP {exc.code}: {body}") from exc
                last_error = ModelClientError(f"Provider HTTP {exc.code}: {body}")
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError) as exc:
                last_error = exc
            if attempt < self.max_retries:
                time.sleep(min(2 ** attempt, 8))
        raise ModelClientError(f"Model request failed after retries: {last_error}") from last_error
