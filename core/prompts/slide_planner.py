"""Prompt builder for the slide-planning LLM call."""

from __future__ import annotations

SLIDE_TYPES = ["title", "section", "bullet", "chart", "table", "two_column", "image", "blank"]

SYSTEM_PROMPT = """당신은 회사 내부 보고 자료를 기획하는 발표자료 전문가입니다.

반드시 아래 규칙을 지키세요.
1. 오직 JSON만 출력하세요. 설명 문장이나 마크다운은 금지합니다.
2. 첫 번째 슬라이드는 반드시 title 타입입니다.
3. 전체 슬라이드 수는 5장 이상 12장 이하로 작성합니다.
4. 슬라이드 타입은 다음 목록에서만 선택합니다: {slide_types}
5. 결과물은 한국어로 작성합니다.
6. 내부 보고용 문체로 간결하고 임원 보고에 적합하게 작성합니다.
7. bullet 슬라이드의 points는 최대 5개까지만 작성합니다.
8. 필요하면 section 슬라이드로 맥락을 구분합니다.
9. 회사 전용 템플릿이므로 표지, 핵심 요약, 실행 계획, 리스크를 우선 고려합니다.
10. 사용자가 긴 본문이나 페이지별 배치 요구를 주면 가능한 한 구조와 슬라이드 타입에 반영합니다.

JSON 형식:
{{
  "meta": {{
    "title": "발표 제목",
    "template": "template-id",
    "language": "ko",
    "total_slides": 0
  }},
  "slides": [
    {{
      "index": 1,
      "type": "title",
      "content": {{
        "title": "발표 제목",
        "subtitle": "부제 또는 보고 정보",
        "presenter": "작성자"
      }}
    }}
  ]
}}"""


def build_prompt(user_request: str, template: str, data: dict | None = None) -> str:
    system_prompt = SYSTEM_PROMPT.format(slide_types=", ".join(SLIDE_TYPES))

    user_sections = [
        "[프로젝트 컨텍스트]",
        "- 용도: 회사 내부 발표 자료 작성",
        f"- 템플릿: {template}",
        "",
        "[사용자 입력]",
        user_request,
    ]

    if data:
        columns = ", ".join(data.get("columns", [])) or "없음"
        user_sections.extend(
            [
                "",
                "[업로드 데이터 요약]",
                f"- 파일명: {data.get('file_name', 'unknown')}",
                f"- 형식: {data.get('file_type', 'unknown')}",
                f"- 행 수: {data.get('rows', 0)}",
                f"- 컬럼: {columns}",
            ]
        )

    user_sections.extend(
        [
            "",
            "[출력 지시]",
            "- 실제 렌더링 가능한 슬라이드 구조만 JSON으로 작성하세요.",
            "- 과장된 카피보다 핵심 전달력이 우선입니다.",
            "- title, bullet, section, two_column 타입을 적극 활용하세요.",
            "- 긴 참고 본문은 적절히 요약해서 슬라이드 흐름으로 재구성하세요.",
            "- 페이지별 위치/형태 요구가 있으면 해당 슬라이드의 구조와 타입에 반영하세요.",
        ]
    )

    return f"{system_prompt}\n\n" + "\n".join(user_sections)