"""
CropNet AI — LLM Service Schemas & Runtime Telemetry Models.

Defines:
1. LlmStructuredAdvisoryPayload: Pydantic schema passed directly as a JSON schema
   dictionary to local Ollama (Qwen3:8B) for grammar-constrained generation.
2. TelemetryCounter: Runtime telemetry tracking live Qwen invocations, deterministic
   fallback invocations, categorized fallback reasons, and execution latencies.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class LlmStructuredAdvisoryPayload(BaseModel):
    """
    Structured advisory payload for JSON-Schema-constrained generation by Qwen3:8B.
    Passed directly to Ollama `format` parameter via `LlmStructuredAdvisoryPayload.model_json_schema()`.
    Enforces concise, context-aware structure: direct_answer, key_reasons, recommended_action, limitations.
    """
    title: Optional[str] = Field(
        default="Advisory",
        max_length=80,
        description="Short descriptive advisory title (2-6 words) in requested language"
    )
    direct_answer: str = Field(
        ...,
        max_length=250,
        description="Direct 1-2 sentence answer (approx 20-50 words) addressing the farmer's specific inquiry first"
    )
    key_reasons: Optional[List[str]] = Field(
        default_factory=list,
        max_length=3,
        description="At most 2-3 short bullet reasons; empty in QUICK mode unless strictly necessary"
    )
    recommended_action: Optional[str] = Field(
        default=None,
        max_length=150,
        description="One practical next action when relevant"
    )
    limitations: Optional[List[str]] = Field(
        default_factory=list,
        max_length=2,
        description="Verified limiting factors, risks, or critical constraints if applicable"
    )
    response_mode: Optional[str] = Field(
        default="QUICK",
        description="'QUICK' (default, ~30-60 words), 'STANDARD' (~80-120 words), or 'DETAILED'"
    )
    what_this_means: Optional[str] = Field(
        default="",
        max_length=350,
        description="Agronomic explanation only when in STANDARD or DETAILED mode"
    )
    what_needs_attention: Optional[List[str]] = Field(
        default_factory=list,
        max_length=3,
        description="Key limiting factors or constraints"
    )
    next_steps: Optional[List[str]] = Field(
        default_factory=list,
        max_length=3,
        description="Practical next steps for the farmer"
    )
    missing_information: Optional[List[str]] = Field(
        default_factory=list,
        max_length=3,
        description="Disclosed missing measurements or unverified items"
    )


class TelemetryCounter(BaseModel):
    """
    Thread-safe runtime telemetry tracker recording live vs fallback invocation counts,
    granular fallback reasons, and empirical latency statistics.
    """
    total_requests: int = 0
    live_qwen_invocations: int = 0
    live_qwen_successes: int = 0
    fallback_invocations: int = 0
    fallback_reasons: Dict[str, int] = Field(
        default_factory=lambda: {
            "offline": 0,
            "timeout": 0,
            "connection_refused": 0,
            "empty_response": 0,
            "json_decode_error": 0,
            "pydantic_validation_error": 0,
            "guardrail_violation": 0,
            "unspecified_error": 0,
        }
    )
    total_live_latency_seconds: float = 0.0
    total_fallback_latency_seconds: float = 0.0

    @property
    def mean_live_latency_seconds(self) -> float:
        if self.live_qwen_successes == 0:
            return 0.0
        return self.total_live_latency_seconds / self.live_qwen_successes

    @property
    def mean_fallback_latency_seconds(self) -> float:
        if self.fallback_invocations == 0:
            return 0.0
        return self.total_fallback_latency_seconds / self.fallback_invocations

    def record_live_success(self, latency: float = 0.0) -> None:
        """Record a successful live Qwen3:8B generation."""
        self.total_requests += 1
        self.live_qwen_invocations += 1
        self.live_qwen_successes += 1
        self.total_live_latency_seconds += max(0.0, latency)

    def record_fallback(
        self,
        reason: str,
        latency: float = 0.0,
        live_attempted: bool = False
    ) -> None:
        """
        Record a deterministic fallback invocation with explicit categorized reason.
        If live_attempted is True, Ollama was invoked but failed (timeout/guardrail/etc).
        If False, fallback was immediate (e.g. Ollama daemon offline).
        """
        self.total_requests += 1
        if live_attempted:
            self.live_qwen_invocations += 1
        self.fallback_invocations += 1

        norm_reason = reason if reason in self.fallback_reasons else "unspecified_error"
        self.fallback_reasons[norm_reason] = self.fallback_reasons.get(norm_reason, 0) + 1
        self.total_fallback_latency_seconds += max(0.0, latency)

    def reset(self) -> None:
        """Reset all counters to initial state."""
        self.total_requests = 0
        self.live_qwen_invocations = 0
        self.live_qwen_successes = 0
        self.fallback_invocations = 0
        for k in self.fallback_reasons:
            self.fallback_reasons[k] = 0
        self.total_live_latency_seconds = 0.0
        self.total_fallback_latency_seconds = 0.0

    def snapshot(self) -> Dict[str, Any]:
        """Return an immutable dictionary snapshot of telemetry status."""
        return {
            "total_requests": self.total_requests,
            "live_qwen_invocations": self.live_qwen_invocations,
            "live_qwen_successes": self.live_qwen_successes,
            "fallback_invocations": self.fallback_invocations,
            "fallback_reasons": dict(self.fallback_reasons),
            "mean_live_latency_seconds": round(self.mean_live_latency_seconds, 3),
            "mean_fallback_latency_seconds": round(self.mean_fallback_latency_seconds, 3),
        }
