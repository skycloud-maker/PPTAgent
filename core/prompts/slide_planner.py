"""
core/prompts/slide_planner.py
슬라이드 기획 프롬프트
모든 프롬프트는 코드 인라인이 아닌 이 파일에서 관리한다 (AGENTS.md)
"""

import json


SLIDE_TYPES = [
    "title", "section", "bullet", "chart",
    "table", "two_column", "image", "blank"
]

SYSTEM_PROMPT = """당신은 한국 비즈니스 환경에 맞는 PPT 슬라이드 구조를 기획하는 전문가입니다.

규칙:
1. 반드시 JSON 형식으로만 응답하세요 (마크다운 코드블록 포함 가능)
2. 슬라이드는 최소 5장, 최대 15장
3. 첫 번째 슬라이드는 반드시 title 타입
4. 슬라이드 타입은 다음 중에서만 선택: {slide_types}
5. 한국어로 내용 작성
6. 불릿 포인트는 슬라이드당 최대 5개
7. 제목은 20자 이하

JSON 구조:
{{
  "meta": {{
    "title": "장표 제목",
    "template": "템플릿명",
    "language": "ko",
    "total_slides": 슬라이드수
  }},
  "slides": [
    {{
      "index": 1,
      "type": "title",
      "content": {{
        "title": "제목",
        "subtitle": "부제목",
        "presenter": "발표자"
      }}
    }},
    ...
  ]
}}"""


def build_prompt(
    user_request: str,
    template: str,
    data: dict | None = None,
) -> str:
    """
    슬라이드 기획 프롬프트를 생성한다.

    Args:
        user_request: 사용자 입력 내용
        template: 선택된 템플릿
        data: 데이터 파일 내용 (선택)

    Returns:
        str: 완성된 프롬프트
    """
    system = SYSTEM_PROMPT.format(slide_types=", ".join(SLIDE_TYPES))

    user_parts = [
        f"템플릿: {template}",
        f"요청 내용:\n{user_request}",
    ]

    if data:
        # 데이터는 구조(컬럼명, 행 수)만 전달 — 내용 최소화 (SECURITY.md)
        columns = list(data.keys()) if isinstance(data, dict) else []
        user_parts.append(f"데이터 컬럼: {', '.join(columns)}")

    user_message = "\n\n".join(user_parts)
    user_message += "\n\n위 내용을 바탕으로 슬라이드 구조를 JSON으로 생성해주세요."

    return f"{system}\n\n{user_message}"
