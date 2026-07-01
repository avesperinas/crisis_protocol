"""Anthropic SDK wrapper.

Single async client used across the app. Handles:
- Model identifiers (Haiku 4.5, Sonnet 4.6, Opus 4.7).
- Prompt-caching helper: system blocks marked with cache_control.
- Token-usage logging per call (input/output/cache_read + estimated $).
- Simple retry (one extra attempt after a 1s pause) before bubbling up.

The caller is responsible for prompt rendering. This module just sends
the request, logs, and returns the text.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Literal

from anthropic import APIError, AsyncAnthropic

logger = logging.getLogger("crisis.ai")


class Models:
    HAIKU = "claude-haiku-4-5-20251001"
    SONNET = "claude-sonnet-4-6"
    OPUS = "claude-opus-4-7"


# Per-million-token pricing (USD). Updated when Anthropic publishes changes.
# These are estimates for accounting purposes only.
_PRICING = {
    Models.HAIKU: {"input": 1.0, "output": 5.0, "cache_read": 0.10},
    Models.SONNET: {"input": 3.0, "output": 15.0, "cache_read": 0.30},
    Models.OPUS: {"input": 15.0, "output": 75.0, "cache_read": 1.50},
}


@dataclass(frozen=True)
class UsageRecord:
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    latency_ms: int
    estimated_cost_usd: float


def _estimate_cost(model: str, in_tok: int, out_tok: int, cache_read_tok: int) -> float:
    p = _PRICING.get(model)
    if not p:
        return 0.0
    return (
        in_tok * p["input"] + out_tok * p["output"] + cache_read_tok * p["cache_read"]
    ) / 1_000_000


SystemBlock = str | list[dict]
"""A system prompt can be a plain string, or a list of cacheable content blocks:
    [{"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}}]
"""


class ClaudeClient:
    def __init__(self, api_key: str):
        self._client = AsyncAnthropic(api_key=api_key)
        self._usage: list[UsageRecord] = []

    @property
    def usage(self) -> list[UsageRecord]:
        return list(self._usage)

    def total_cost_usd(self) -> float:
        return sum(r.estimated_cost_usd for r in self._usage)

    async def call(
        self,
        *,
        model: str,
        system: SystemBlock | None = None,
        user_message: str,
        max_tokens: int = 1500,
        temperature: float = 0.7,
        prefill: str | None = None,
    ) -> str:
        """Single round trip. Retries once on APIError or TimeoutError.

        `prefill` pre-seeds the assistant turn (e.g. '{\"') to force JSON output.
        The prefill string is prepended to the returned text automatically.
        """
        attempt = 0
        last_err: Exception | None = None
        while attempt < 2:
            try:
                return await self._call_once(
                    model=model,
                    system=system,
                    user_message=user_message,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    prefill=prefill,
                )
            except (APIError, asyncio.TimeoutError) as e:
                last_err = e
                attempt += 1
                logger.warning(
                    "Claude call failed (attempt %d/2): %s. Retrying in 1s.", attempt, e
                )
                if attempt < 2:
                    await asyncio.sleep(1)
        # Out of retries — raise.
        assert last_err is not None
        raise last_err

    async def _call_once(
        self,
        *,
        model: str,
        system: SystemBlock | None,
        user_message: str,
        max_tokens: int,
        temperature: float,
        prefill: str | None = None,
    ) -> str:
        messages: list[dict] = [{"role": "user", "content": user_message}]
        if prefill:
            messages.append({"role": "assistant", "content": prefill})
        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system is not None:
            kwargs["system"] = system

        started = time.monotonic()
        response = await self._client.messages.create(**kwargs)
        latency_ms = int((time.monotonic() - started) * 1000)

        usage = getattr(response, "usage", None)
        in_tok = getattr(usage, "input_tokens", 0) if usage else 0
        out_tok = getattr(usage, "output_tokens", 0) if usage else 0
        cache_read = getattr(usage, "cache_read_input_tokens", 0) if usage else 0
        cost = _estimate_cost(model, in_tok, out_tok, cache_read)

        record = UsageRecord(
            model=model,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cache_read_tokens=cache_read,
            latency_ms=latency_ms,
            estimated_cost_usd=cost,
        )
        self._usage.append(record)
        logger.info(
            "Claude call: model=%s in=%d out=%d cache_read=%d ms=%d cost=$%.5f",
            model,
            in_tok,
            out_tok,
            cache_read,
            latency_ms,
            cost,
        )

        # response.content is a list of content blocks; we return the first text block.
        if not response.content:
            return prefill or ""
        first = response.content[0]
        text = getattr(first, "text", "")
        # When prefilling, Claude returns only the continuation; prepend the seed.
        return (prefill + text) if prefill else text


def cacheable(text: str) -> list[dict]:
    """Wrap a stable string as a single cacheable system block."""
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


__all__ = [
    "ClaudeClient",
    "Models",
    "UsageRecord",
    "cacheable",
]
