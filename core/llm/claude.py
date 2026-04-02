"""
core/llm/claude.py
Claude API 어댑터
LLMInterface를 구현한 Claude 전용 어댑터
"""

import json
import logging
import os
import time

import anthropic
from dotenv import load_dotenv
from pydantic import ValidationError

from core.llm.interface import LLMInterface
from core.schema import SlideSchema

load_dotenv()

logger = logging.getLogger(__name__)

# RELIABILITY.md 기준
MAX_RETRIES = 2
RETRY_DELAY = 2
TIMEOUT = 30


class ClaudeAdapter(LLMInterface):
    """Claude API를 사용하는 LLM 어댑터"""

    def __init__(self) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"

    def plan_slides(
        self,
        user_request: str,
        template: str,
        data: dict | None = None,
    ) -> SlideSchema:
        """
        Claude API를 호출하여 슬라이드 스키마를 생성한다.
        실패 시 최대 MAX_RETRIES회 재시도한다.
        """
        prompt = self._build_prompt(user_request, template, data)

        for attempt in range(MAX_RETRIES + 1):
            try:
                start = time.time()
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    timeout=TIMEOUT,
                    messages=[{"role": "user", "content": prompt}],
                )
                elapsed = round(time.time() - start, 2)

                # 토큰 사용량만 로그 기록 (내용 제외 — SECURITY.md)
                usage = response.usage
                logger.info(
                    f"Claude API 응답 완료 | "
                    f"tokens={usage.input_tokens + usage.output_tokens} | "
                    f"elapsed={elapsed}s | attempt={attempt + 1}"
                )

                return self._parse_response(response.content[0].text)

            except anthropic.APITimeoutError:
                logger.warning(f"Claude API 타임아웃 | attempt={attempt + 1}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                else:
                    raise RuntimeError("슬라이드 생성에 실패했어요. 잠시 후 다시 시도해주세요.")

            except anthropic.RateLimitError:
                logger.warning(f"Claude API Rate limit | attempt={attempt + 1}")
                if attempt < MAX_RETRIES:
                    time.sleep(10)
                else:
                    raise RuntimeError("요청이 너무 많아요. 잠시 후 다시 시도해주세요.")

            except anthropic.APIError as e:
                logger.error(f"Claude API 오류 | error={type(e).__name__} | attempt={attempt + 1}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                else:
                    raise RuntimeError("슬라이드 생성에 실패했어요. 잠시 후 다시 시도해주세요.")

        raise RuntimeError("슬라이드 생성에 실패했어요. 잠시 후 다시 시도해주세요.")

    def _parse_response(self, text: str) -> SlideSchema:
        """
        Claude 응답 텍스트에서 JSON을 추출하고 SlideSchema로 검증한다.
        실패 시 최대 3회 재시도 (RELIABILITY.md 기준)
        """
        # JSON 블록 추출
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(text)
            return SlideSchema(**data)
        except (json.JSONDecodeError, ValidationError, KeyError) as e:
            logger.error(f"SlideSchema 파싱 실패 | error={type(e).__name__}")
            raise RuntimeError("슬라이드 구조 생성에 실패했어요. 다시 시도해주세요.")

    def _build_prompt(
        self,
        user_request: str,
        template: str,
        data: dict | None,
    ) -> str:
        """프롬프트 생성 — 실제 프롬프트는 core/prompts/ 에서 관리"""
        from core.prompts.slide_planner import build_prompt
        return build_prompt(user_request, template, data)
