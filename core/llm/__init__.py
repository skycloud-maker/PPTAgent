"""LLM provider factory.

우선순위:
1. LLM_PROVIDER=mock  → MockAdapter (API 키 불필요)
2. OPENAI_API_KEY 있음 → OpenAIAdapter
3. 그 외              → MockAdapter (자동 fallback)
"""

from __future__ import annotations

import logging
import os

from core.llm.interface import LLMInterface

logger = logging.getLogger(__name__)


def get_default_llm() -> LLMInterface:
    """환경변수 기반으로 적절한 LLM 어댑터를 반환한다."""

    provider = os.getenv("LLM_PROVIDER", "").strip().lower()

    # 명시적으로 mock 지정
    if provider == "mock":
        logger.info("LLM_PROVIDER=mock → MockAdapter 사용")
        return _get_mock()

    # OpenAI API 키가 있으면 OpenAI 사용
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key and api_key != "your_openai_api_key_here":
        try:
            from core.llm.openai import OpenAIAdapter
            logger.info("OPENAI_API_KEY 감지 → OpenAIAdapter 사용")
            return OpenAIAdapter()
        except Exception as exc:
            logger.warning("OpenAIAdapter 초기화 실패 → Mock으로 fallback | error=%s", exc)
            return _get_mock()

    # 키 없으면 자동으로 Mock fallback
    logger.info("API 키 없음 → MockAdapter로 자동 fallback (테스트 모드)")
    return _get_mock()


def _get_mock() -> LLMInterface:
    from core.llm.mock_adapter import MockAdapter
    return MockAdapter()
