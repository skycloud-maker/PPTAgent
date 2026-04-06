"""OpenAI adapter for slide planning."""

from __future__ import annotations

import json
import logging
import os
import time

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, AuthenticationError, OpenAI, RateLimitError
from pydantic import ValidationError

from core.llm.interface import LLMInterface
from core.schema import SlideSchema

load_dotenv()

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 2
DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIAdapter(LLMInterface):
    """Plan slide schemas by calling the OpenAI Responses API."""

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key or api_key == "your_openai_api_key_here":
            raise ValueError("OpenAI API 키가 설정되지 않았습니다. .env 파일의 OPENAI_API_KEY를 실제 키로 바꿔주세요.")

        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
        logger.info("OpenAIAdapter initialized | model=%s", self.model)

    def plan_slides(
        self,
        user_request: str,
        template: str,
        data: dict | None = None,
    ) -> SlideSchema:
        prompt = self._build_prompt(user_request, template, data)

        for attempt in range(MAX_RETRIES + 1):
            try:
                started_at = time.time()
                response = self.client.responses.create(
                    model=self.model,
                    input=[
                        {
                            "role": "user",
                            "content": [{"type": "input_text", "text": prompt}],
                        }
                    ],
                )
                elapsed = round(time.time() - started_at, 2)
                logger.info(
                    "OpenAI slide plan completed | model=%s | elapsed=%ss | attempt=%s",
                    self.model,
                    elapsed,
                    attempt + 1,
                )
                return self._parse_response(response.output_text)
            except AuthenticationError as exc:
                logger.error("OpenAI authentication failed | error=%s", type(exc).__name__)
                raise RuntimeError("OpenAI 인증에 실패했습니다. .env의 OPENAI_API_KEY가 올바른지 확인해주세요.")
            except RateLimitError as exc:
                code = None
                try:
                    code = exc.body.get("error", {}).get("code")
                except Exception:
                    code = None
                logger.warning("OpenAI rate/quota issue | code=%s | attempt=%s", code, attempt + 1)
                if code == "insufficient_quota":
                    raise RuntimeError("OpenAI API는 연결되었지만 현재 프로젝트의 API 크레딧/한도가 부족합니다. OpenAI 플랫폼의 Billing 또는 Credits 상태를 확인해주세요.")
                if attempt < MAX_RETRIES:
                    time.sleep(10)
                    continue
                raise RuntimeError("OpenAI 요청 한도에 도달했습니다. 잠시 후 다시 시도해주세요.")
            except APIConnectionError as exc:
                logger.warning("OpenAI connection error | attempt=%s | error=%s", attempt + 1, type(exc).__name__)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS)
                    continue
                raise RuntimeError("OpenAI API 연결에 실패했습니다. 네트워크 상태를 확인해주세요.")
            except APIStatusError as exc:
                logger.error("OpenAI status error | status=%s | attempt=%s", exc.status_code, attempt + 1)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS)
                    continue
                raise RuntimeError(f"OpenAI API 호출이 실패했습니다. status={exc.status_code}")

        raise RuntimeError("슬라이드 구조 생성에 실패했습니다. 잠시 후 다시 시도해주세요.")

    def _parse_response(self, text: str) -> SlideSchema:
        text = text.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0].strip()
        elif text.startswith("```"):
            text = text.split("```", 1)[1].split("```", 1)[0].strip()

        try:
            payload = json.loads(text)
            return SlideSchema(**payload)
        except (json.JSONDecodeError, ValidationError, KeyError) as exc:
            logger.error("Slide schema parse failed | error=%s", type(exc).__name__)
            raise RuntimeError("슬라이드 구조 해석에 실패했습니다. 다시 시도해주세요.")

    def _build_prompt(self, user_request: str, template: str, data: dict | None) -> str:
        from core.prompts.slide_planner import build_prompt

        return build_prompt(user_request, template, data)
