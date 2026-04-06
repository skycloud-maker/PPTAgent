"""LLM provider factory for PPTAgent."""

from __future__ import annotations

import logging
import os

from core.llm.interface import LLMInterface

logger = logging.getLogger(__name__)


def get_default_llm() -> LLMInterface:
    """Return the configured LLM adapter.

    Resolution order:
    1. `LLM_PROVIDER` explicit selection (`openai` or `mock`)
    2. If unset and `OPENAI_API_KEY` exists, use OpenAI
    3. Otherwise fallback to mock for local testing
    """
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    has_openai_key = bool(os.getenv("OPENAI_API_KEY", "").strip())

    logger.info("Resolving LLM provider | LLM_PROVIDER=%s | has_openai_key=%s", provider or "<unset>", has_openai_key)

    if provider == "mock":
        logger.info("Using MockAdapter because LLM_PROVIDER=mock")
        return _get_mock()

    if provider == "openai":
        logger.info("Using OpenAIAdapter because LLM_PROVIDER=openai")
        return _get_openai()

    if provider:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

    if has_openai_key:
        logger.info("Using OpenAIAdapter because OPENAI_API_KEY is configured")
        return _get_openai()

    logger.warning("No explicit provider and no OPENAI_API_KEY; falling back to MockAdapter")
    return _get_mock()



def _get_openai() -> LLMInterface:
    from core.llm.openai import OpenAIAdapter

    return OpenAIAdapter()



def _get_mock() -> LLMInterface:
    from core.llm.mock_adapter import MockAdapter

    return MockAdapter()
