"""Shared interfaces and result types for model providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GenerationResult:
    text: str
    model: str
    prompt_tokens: int | None = None
    generated_tokens: int | None = None
    total_duration_ns: int | None = None


class ModelProvider(Protocol):
    def generate(
        self,
        model: str,
        prompt: str,
        *,
        system: str | None = None,
        num_ctx: int = 2048,
        num_predict: int = 512,
    ) -> GenerationResult:
        """Generate a response for a bounded prompt."""
