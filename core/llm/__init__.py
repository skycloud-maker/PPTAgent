"""Helpers for selecting the active LLM adapter."""

from __future__ import annotations

import os

from core.llm.interface import LLMInterface
from core.llm.openai import OpenAIAdapter


def get_default_llm() -> LLMInterface:
    """Return the configured LLM adapter for the application."""
    provider = os.getenv("PPTAGENT_LLM_PROVIDER", "openai").strip().lower()
    if provider == "openai":
        return OpenAIAdapter()
    if provider == "claude":
        from core.llm.claude import ClaudeAdapter

        return ClaudeAdapter()
    raise ValueError(f"지원하지 않는 LLM provider입니다: {provider}")


__all__ = ["LLMInterface", "OpenAIAdapter", "get_default_llm"]