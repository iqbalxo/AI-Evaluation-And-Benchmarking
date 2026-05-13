import os
import time
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class ModelRequest:
    prompt: str
    model_id: str
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    seed: int | None = None
    timeout_seconds: float = 30.0


@dataclass(frozen=True)
class ModelResponse:
    text: str
    latency_ms: float
    token_usage: int
    raw_usage: dict
    provider: str


class ProviderClientError(RuntimeError):
    pass


class OpenRouterClient:
    url = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")

    def complete(self, request: ModelRequest) -> ModelResponse:
        if not self.api_key:
            raise ProviderClientError("OPENROUTER_API_KEY is not set; add it to .env or your shell environment")
        if not request.model_id:
            raise ProviderClientError("OpenRouter model id is required")

        payload = {
            "model": request.model_id,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        for key in ("temperature", "max_tokens", "top_p", "seed"):
            value = getattr(request, key)
            if value is not None:
                payload[key] = value

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "http://localhost:5173"),
            "X-Title": os.getenv("OPENROUTER_APP_NAME", "AI Evaluation Platform"),
        }

        start_time = time.time()
        try:
            with httpx.Client(timeout=request.timeout_seconds) as client:
                response = client.post(self.url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500] if exc.response is not None else str(exc)
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            raise ProviderClientError(
                f"OpenRouter request failed for {request.model_id}: HTTP {status_code} - {detail}"
            ) from exc
        except Exception as exc:
            raise ProviderClientError(f"OpenRouter request failed for {request.model_id}: {exc}") from exc

        latency_ms = (time.time() - start_time) * 1000
        choices = data.get("choices") or []
        if not choices:
            raise ProviderClientError(f"OpenRouter returned no choices for {request.model_id}")

        text = choices[0].get("message", {}).get("content", "")
        usage = data.get("usage") or {}
        return ModelResponse(
            text=text,
            latency_ms=latency_ms,
            token_usage=int(usage.get("total_tokens") or 0),
            raw_usage=usage,
            provider=data.get("provider") or "openrouter",
        )
