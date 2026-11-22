"""Application metrics shared by the API and ingestion pipeline."""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Protocol

from prometheus_client import Counter, Gauge

LLM_TOKENS = Counter(
    "aegisops_llm_tokens_total",
    "Prompt and completion tokens consumed by LLM calls",
    ("kind",),
)
LLM_COST_USD = Counter("aegisops_llm_cost_usd_total", "Estimated LLM cost in USD")
PII_ENTITIES_REDACTED = Counter(
    "aegisops_pii_entities_redacted_total", "PII entities redacted before indexing"
)
PII_ENTITIES_REDACTED_INDEXED = Gauge(
    "aegisops_pii_entities_redacted_indexed",
    "PII entities redacted in the configured post-mortem index",
)
CIRCUIT_BREAKER_OPEN = Gauge(
    "aegisops_llm_circuit_breaker_open", "Whether the LLM circuit breaker is open"
)
_pii_redaction_count = 0
_pii_redaction_lock = threading.Lock()


def record_pii_entities_redacted(count: int) -> None:
    global _pii_redaction_count
    with _pii_redaction_lock:
        _pii_redaction_count += count
    PII_ENTITIES_REDACTED.inc(count)


def get_pii_entities_redacted() -> int:
    with _pii_redaction_lock:
        return _pii_redaction_count


class Telemetry:
    """Keep a small in-memory latency window and LLM operational totals."""

    def __init__(
        self, latency_window: int = 500, *, cost_pricing_configured: bool = False
    ) -> None:
        self._latencies: deque[float] = deque(maxlen=latency_window)
        self._lock = threading.Lock()
        self.llm_tokens = 0
        self.llm_cost_usd = 0.0
        self.cost_pricing_configured = cost_pricing_configured
        self.pii_entities_redacted = 0
        self.circuit_breaker_open = False

    def record_request(self, duration_seconds: float) -> None:
        with self._lock:
            self._latencies.append(duration_seconds)

    def p95_latency_seconds(self) -> float | None:
        with self._lock:
            if not self._latencies:
                return None
            ordered = sorted(self._latencies)
        index = max(0, int(len(ordered) * 0.95 + 0.999999) - 1)
        return ordered[index]

    def record_llm_usage(self, prompt_tokens: int, completion_tokens: int, cost: float) -> None:
        with self._lock:
            self.llm_tokens += prompt_tokens + completion_tokens
            self.llm_cost_usd += cost
        LLM_TOKENS.labels(kind="prompt").inc(prompt_tokens)
        LLM_TOKENS.labels(kind="completion").inc(completion_tokens)
        LLM_COST_USD.inc(cost)

    def record_pii_redactions(self, count: int) -> None:
        with self._lock:
            self.pii_entities_redacted += count
        record_pii_entities_redacted(count)

    def set_circuit_breaker(self, is_open: bool) -> None:
        with self._lock:
            self.circuit_breaker_open = is_open
        CIRCUIT_BREAKER_OPEN.set(1 if is_open else 0)

    def snapshot(
        self, indexed_pii_count: int | None = None
    ) -> dict[str, float | int | bool | None | str]:
        with self._lock:
            tokens = self.llm_tokens
            cost = self.llm_cost_usd
            breaker_open = self.circuit_breaker_open
        pii_count = (
            get_pii_entities_redacted()
            if indexed_pii_count is None
            else indexed_pii_count
        )
        if indexed_pii_count is not None:
            PII_ENTITIES_REDACTED_INDEXED.set(indexed_pii_count)
        return {
            "api_p95_latency_seconds": self.p95_latency_seconds(),
            "llm_tokens_total": tokens,
            "llm_cost_usd_total": cost,
            "cost_pricing_configured": self.cost_pricing_configured,
            "circuit_breaker_status": "open" if breaker_open else "closed",
            "pii_entities_redacted_total": pii_count,
        }


class CircuitOpenError(RuntimeError):
    """Raised when an LLM request is rejected by the circuit breaker."""


class CompletionLike(Protocol):
    prompt_tokens: int
    completion_tokens: int


class ChatClientLike(Protocol):
    def complete(self, prompt: str) -> CompletionLike: ...


class InstrumentedChatClient:
    def __init__(
        self,
        client: ChatClientLike,
        telemetry: Telemetry,
        *,
        input_cost_per_million: float = 0.0,
        output_cost_per_million: float = 0.0,
        failure_threshold: int = 3,
        reset_timeout_seconds: float = 30.0,
    ) -> None:
        self._client = client
        self._telemetry = telemetry
        self._input_rate = input_cost_per_million
        self._output_rate = output_cost_per_million
        self._failure_threshold = failure_threshold
        self._reset_timeout_seconds = reset_timeout_seconds
        self._failures = 0
        self._opened_at: float | None = None
        self._breaker_lock = threading.Lock()

    def complete(self, prompt: str) -> CompletionLike:
        now = time.monotonic()
        with self._breaker_lock:
            if self._opened_at is not None:
                if now - self._opened_at < self._reset_timeout_seconds:
                    raise CircuitOpenError("LLM circuit breaker is open")
                self._opened_at = None
                self._failures = 0
                self._telemetry.set_circuit_breaker(False)
        try:
            result = self._client.complete(prompt)
        except Exception:
            with self._breaker_lock:
                self._failures += 1
                if self._failures >= self._failure_threshold:
                    self._opened_at = time.monotonic()
                    self._telemetry.set_circuit_breaker(True)
            raise

        with self._breaker_lock:
            self._failures = 0
        prompt_tokens = int(result.prompt_tokens)
        completion_tokens = int(result.completion_tokens)
        cost = (
            prompt_tokens * self._input_rate + completion_tokens * self._output_rate
        ) / 1_000_000
        self._telemetry.record_llm_usage(prompt_tokens, completion_tokens, cost)
        return result